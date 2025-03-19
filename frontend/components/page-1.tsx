"use client"

import type React from "react"
import { useState, useEffect, useRef } from "react"
import { useToast } from "@/components/ui/use-toast"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs"
import { Card, CardContent } from "@/components/ui/card"
import { Loader2 } from "lucide-react"
import { ChatDisplay } from "@/components/ui/chat-display"
import * as api from "@/lib/api"

const API_BASE_URL = "http://localhost:8080"
const WS_BASE_URL = "ws://localhost:8080"

interface Message {
  role: string
  content: string
}

export function Page1() {
  const { toast } = useToast()
  const [text, setText] = useState("")
  const [files, setFiles] = useState<{ doc1: File | null; doc2: File | null }>({ doc1: null, doc2: null })
  const [conversations, setConversations] = useState<Record<string, Message[]>>({})
  const [conversationNames, setConversationNames] = useState<string[]>([])
  const [activeTab, setActiveTab] = useState<string>("")
  const [uploading, setUploading] = useState(false)
  const [conversationsLoaded, setConversationsLoaded] = useState(false)
  const fileInputRef1 = useRef<HTMLInputElement>(null)
  const fileInputRef2 = useRef<HTMLInputElement>(null)
  const socketsRef = useRef<Record<string, WebSocket>>({})
  const abortControllerRef = useRef<AbortController | null>(null)
  const pollingTimeoutRef = useRef<NodeJS.Timeout | null>(null)

  // Fetch conversations only on initial load
  useEffect(() => {
    let isComponentMounted = true;

    async function fetchConversationNames() {
      // Cancel any in-flight requests
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }

      // Create a new AbortController for this request
      abortControllerRef.current = new AbortController();

      try {
        const response = await fetch(`${API_BASE_URL}/conversations`, {
          signal: abortControllerRef.current.signal
        });
        
        if (!response.ok) {
          throw new Error("Failed to fetch conversation names");
        }
        
        const data = await response.json();
        const names = data.content || [];
        
        if (isComponentMounted) {
          setConversationNames(names);
          setActiveTab(prevActiveTab => {
            if (!prevActiveTab && names.length > 0) {
              return names[0];
            }
            return prevActiveTab;
          });
          
          // Mark conversations as loaded to stop polling
          setConversationsLoaded(true);
        }
      } catch (error) {
        if (error instanceof Error && error.name !== 'AbortError') {
          console.error("Error fetching conversation names:", error);
          if (isComponentMounted) {
            toast({
              variant: "destructive",
              title: "Error",
              description: "Failed to fetch conversation names. Please try again later.",
            });
          }
        }
      } finally {
        // Clear the controller reference if this request completed or was aborted
        if (abortControllerRef.current && abortControllerRef.current.signal.aborted) {
          abortControllerRef.current = null;
        }
      }
    }

    // Only fetch if conversations haven't been loaded yet
    if (!conversationsLoaded) {
      fetchConversationNames();
    }
    
    // Cleanup function
    return () => {
      isComponentMounted = false;
      
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [toast, conversationsLoaded]);

  // Function to manually refresh conversations if needed
  const refreshConversations = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/conversations`);
      if (!response.ok) {
        throw new Error("Failed to fetch conversation names");
      }
      
      const data = await response.json();
      const names = data.content || [];
      
      setConversationNames(names);
      if (names.length > 0 && !activeTab) {
        setActiveTab(names[0]);
      }
    } catch (error) {
      console.error("Error refreshing conversations:", error);
      toast({
        variant: "destructive",
        title: "Error",
        description: "Failed to refresh conversations.",
      });
    }
  };

  // Create WebSocket connections for each conversation
  useEffect(() => {
    function createWebSocketForConversation(conversationName: string) {
      // Properly encode the conversation name for WebSocket URL
      const encodedName = encodeURIComponent(conversationName)
      const newSocket = new WebSocket(`${WS_BASE_URL}/ws/conversation/${encodedName}`)

      newSocket.onmessage = (event) => {
        const data: Message[] = JSON.parse(event.data)
        setConversations((prevConversations) => ({
          ...prevConversations,
          [conversationName]: data,
        }))
      }

      newSocket.onopen = () => {
        console.log(`WebSocket connection opened for ${conversationName}`)
      }

      newSocket.onclose = () => {
        console.log(`WebSocket connection closed for ${conversationName}`)
        toast({
          variant: "destructive",
          title: "Connection Closed",
          description: `The connection for ${conversationName} has been closed. Please refresh the page.`,
        })
      }

      newSocket.onerror = (error) => {
        console.error(`WebSocket error for ${conversationName}:`, error)
        toast({
          variant: "destructive",
          title: "Connection Error",
          description: `An error occurred with the WebSocket connection for ${conversationName}. Please try again later.`,
        })
      }

      socketsRef.current[conversationName] = newSocket
    }

    conversationNames.forEach((name) => {
      createWebSocketForConversation(name)
    })

    return () => {
      Object.values(socketsRef.current).forEach((socket) => socket.close())
    }
  }, [conversationNames, toast])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>, docNumber: 1 | 2) => {
    const file = e.target.files?.[0]
    if (file) {
      setFiles((prev) => ({
        ...prev,
        [`doc${docNumber}`]: file,
      }))
    }
  }

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value)
  }

  const handleCombinedSubmit = async () => {
    const hasFiles = files.doc1 && files.doc2;
    const hasText = !!text.trim();

    // Ensure at least one type of content is provided
    if (!hasFiles && !hasText) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Please provide either files, text, or both before submitting.",
      });
      return;
    }

    try {
      setUploading(true);
      
      // First upload documents if provided
      if (hasFiles) {
        await api.uploadDocuments(files.doc1!, files.doc2!);
        toast({
          title: "Success",
          description: "Documents uploaded successfully",
        });
        
        // Reset file inputs
        if (fileInputRef1.current) fileInputRef1.current.value = "";
        if (fileInputRef2.current) fileInputRef2.current.value = "";
        setFiles({ doc1: null, doc2: null });
      }
      
      // Then upload text if provided
      if (hasText) {
        await api.uploadText(text);
        toast({
          title: "Success",
          description: "Text uploaded successfully",
        });
        setText("");
      }
      
      // Refresh conversations after all uploads complete
      await refreshConversations();
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to process submission",
      });
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-6 md:grid-cols-[2fr_1fr]">
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Enter Job Description</h2>
          <Textarea
            value={text}
            onChange={handleTextChange}
            className="min-h-[200px]"
            placeholder="Enter your job description here..."
          />
        </div>
        <div className="space-y-4">
          <div className="space-y-2">
            <h2 className="text-lg font-semibold">Upload your CV and Cover Letter</h2>
            <div className="grid gap-4">
              <div>
                <input
                  type="file"
                  id="doc1"
                  className="hidden"
                  ref={fileInputRef1}
                  onChange={(e) => handleFileChange(e, 1)}
                />
                <Button variant="outline" className="w-full" onClick={() => fileInputRef1.current?.click()}>
                  {files.doc1 ? files.doc1.name : "Select CV"}
                </Button>
              </div>
              <div>
                <input
                  type="file"
                  id="doc2"
                  className="hidden"
                  ref={fileInputRef2}
                  onChange={(e) => handleFileChange(e, 2)}
                />
                <Button variant="outline" className="w-full" onClick={() => fileInputRef2.current?.click()}>
                  {files.doc2 ? files.doc2.name : "Select Cover Letter"}
                </Button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Combined Submit Button */}
      <Button 
        onClick={handleCombinedSubmit} 
        disabled={uploading || (!text.trim() && (!files.doc1 || !files.doc2))}
        className="w-full"
      >
        {uploading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Uploading...
          </>
        ) : (
          "Submit"
        )}
      </Button>

      <Card>
        <CardContent className="pt-6">
          <Tabs value={activeTab} onValueChange={setActiveTab}>
            <TabsList className="w-full justify-start">
              {conversationNames.map((name) => (
                <TabsTrigger key={name} value={name} className="flex-1">
                  {name}
                </TabsTrigger>
              ))}
            </TabsList>
            {conversationNames.map((name) => (
              <TabsContent key={name} value={name} className="mt-4 p-4 border rounded-lg">
                <ChatDisplay messages={conversations[name] || []} />
              </TabsContent>
            ))}
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}