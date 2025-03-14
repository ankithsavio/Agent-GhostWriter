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
  const fileInputRef1 = useRef<HTMLInputElement>(null)
  const fileInputRef2 = useRef<HTMLInputElement>(null)
  const socketsRef = useRef<Record<string, WebSocket>>({})

  useEffect(() => {
    let isComponentMounted = true;
    const POLLING_INTERVAL = 5000; // 5 seconds

    async function fetchConversationNames() {
      try {
        const response = await fetch(`${API_BASE_URL}/conversations`)
        if (!response.ok) {
          throw new Error("Failed to fetch conversation names")
        }
        const data = await response.json()
        const names = data.content || [] 
        
        if (isComponentMounted) {
          setConversationNames(names)
          setActiveTab(prevActiveTab => {
            if (!prevActiveTab && names.length > 0) {
              return names[0];
            }
            return prevActiveTab;
          });
        }
      } catch (error) {
        console.error("Error fetching conversation names:", error)
        if (isComponentMounted) {
          toast({
            variant: "destructive",
            title: "Error",
            description: "Failed to fetch conversation names. Please try again later.",
          })
        }
      }
    }

    // Initial fetch
    fetchConversationNames();
    
    // Set up polling interval
    const intervalId = setInterval(fetchConversationNames, POLLING_INTERVAL);

    // Clean up interval when component unmounts
    return () => {
      isComponentMounted = false;
      clearInterval(intervalId);
    };
  }, [toast])

  useEffect(() => {
    function createWebSocketForConversation(conversationName: string) {
      const newSocket = new WebSocket(`${WS_BASE_URL}/ws/conversation/${conversationName}`)

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

  async function handleDocumentsUpload() {
    if (!files.doc1 || !files.doc2) {
      toast({
        variant: "destructive",
        title: "Error",
        description: "Please select both documents before uploading.",
      })
      return
    }

    try {
      setUploading(true)
      await api.uploadDocuments(files.doc1, files.doc2)
      toast({
        title: "Success",
        description: "Documents uploaded successfully",
      })
      // Reset file inputs
      if (fileInputRef1.current) fileInputRef1.current.value = ""
      if (fileInputRef2.current) fileInputRef2.current.value = ""
      setFiles({ doc1: null, doc2: null })
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to upload documents",
      })
    } finally {
      setUploading(false)
    }
  }

  async function handleTextSubmit() {
    if (!text.trim()) return

    try {
      setUploading(true)
      await api.uploadText(text)
      toast({
        title: "Success",
        description: "Text uploaded successfully",
      })
      setText("")
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to upload text",
      })
    } finally {
      setUploading(false)
    }
  }

  const handleTextChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setText(e.target.value)
  }

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
          <Button onClick={handleTextSubmit} disabled={uploading || !text.trim()}>
            {uploading ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Uploading...
              </>
            ) : (
              "Submit Text"
            )}
          </Button>
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
                  {files.doc1 ? files.doc1.name : "Select Doc 1"}
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
                  {files.doc2 ? files.doc2.name : "Select Doc 2"}
                </Button>
              </div>
              <Button onClick={handleDocumentsUpload} disabled={uploading || !files.doc1 || !files.doc2}>
                {uploading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Uploading...
                  </>
                ) : (
                  "Upload"
                )}
              </Button>
            </div>
          </div>
        </div>
      </div>

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