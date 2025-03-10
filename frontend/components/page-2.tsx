"use client"

import { useState, useEffect, useRef } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Loader2 } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import * as api from "@/lib/api"
import ReactDiffViewer from "react-diff-viewer"
import { Badge } from "@/components/ui/badge"
import { AlertCircle, CheckCircle, Edit, XCircle } from "lucide-react"
import { Textarea } from "@/components/ui/textarea"

const WS_BASE_URL = "ws://localhost:8080"
const API_BASE_URL = "http://localhost:8080"


interface Suggestion {
  id: number;
  content: string;
  replacement: string;
  reason: string;
}

export function Page2() {
  const { toast } = useToast()
  const [selectedDoc, setSelectedDoc] = useState<1 | 2>(1)
  const [documentContent, setDocumentContent] = useState("")
  const [loading, setLoading] = useState(false)
  const [personaList, setPersonaList] = useState<string[]>([])
  const [personasLoading, setPersonasLoading] = useState(false)
  const [selectedPersona, setSelectedPersona] = useState<string | null>(null)
  const [suggestions, setSuggestions] = useState<Suggestion[]>([])
  const [suggestionLoading, setSuggestionLoading] = useState(false)
  const [editedReplacements, setEditedReplacements] = useState<Record<string | number, string>>({});
  const [editMode, setEditMode] = useState<Record<string | number, boolean>>({});
  const documentSocketRef = useRef<WebSocket | null>(null)
  const suggestionSocketRef = useRef<WebSocket | null>(null)

  // Fetch personas from backend
  useEffect(() => {
    const fetchPersonas = async () => {
      setPersonasLoading(true);
      try {
        const response = await fetch(`${API_BASE_URL}/conversations`);
        const data = await response.json();
        if (data.content) {
          setPersonaList(data.content);
        }
      } catch (error) {
        console.error("Failed to fetch personas:", error);
        toast({
          variant: "destructive",
          title: "Error",
          description: "Failed to fetch personas. Please try again.",
        });
      } finally {
        setPersonasLoading(false);
      }
    };

    fetchPersonas();
  }, [toast]);

  // Document WebSocket connection
  useEffect(() => {
    if (documentSocketRef.current) {
      documentSocketRef.current.close();
    }

    setLoading(true);
    const socket = api.createDocumentWebSocket(selectedDoc);
    documentSocketRef.current = socket;

    socket.onopen = () => {
      console.log(`WebSocket connection opened for document ${selectedDoc}`);
    }

    socket.onmessage = (event) => {
      setDocumentContent(event.data);
      setLoading(false);
    }

    socket.onclose = () => {
      console.log(`WebSocket connection closed for document ${selectedDoc}`);
    }

    socket.onerror = (error) => {
      console.error(`WebSocket error for document ${selectedDoc}:`, error);
      toast({
        variant: "destructive",
        title: "Connection Error",
        description: `Failed to connect to document ${selectedDoc}`,
      });
      setLoading(false);
    }

    return () => {
      if (socket) {
        socket.close();
      }
    }
  }, [selectedDoc, toast]);

  // Suggestion WebSocket connection
  useEffect(() => {
    // Close previous connection if it exists
    if (suggestionSocketRef.current) {
      suggestionSocketRef.current.close();
      suggestionSocketRef.current = null;
    }

    // Only create a connection if a persona is selected
    if (!selectedPersona) return;

    const socket = new WebSocket(`${WS_BASE_URL}/ws/suggestions/${selectedPersona}/${selectedDoc}`);
    suggestionSocketRef.current = socket;

    socket.onopen = () => {
      console.log(`Suggestion WebSocket connection opened for ${selectedPersona}`);
    }

    socket.onmessage = (event) => {
      try {
        const response = JSON.parse(event.data);
        
        // Handle end of suggestions
        if (response.end) {
          toast({
            title: "No more suggestions",
            description: response.message,
          });
          setSuggestionLoading(false);
          return;
        }
        
        // Handle error messages
        if (response.error) {
          toast({
            variant: "destructive",
            title: "Error",
            description: response.error,
          });
          setSuggestionLoading(false);
          return;
        }
        
        // Handle regular suggestions
        if (response.content && response.replacement) {
          setSuggestions(prev => [...prev, {
            ...response,
            id: Date.now() + Math.random()
          }]);
        }
        
        setSuggestionLoading(false);
      } catch (error) {
        console.error("Failed to parse suggestion:", error);
        setSuggestionLoading(false);
      }
    }

    socket.onclose = () => {
      console.log(`Suggestion WebSocket connection closed for ${selectedPersona}`);
    }

    socket.onerror = (error) => {
      console.error(`Suggestion WebSocket error for ${selectedPersona}:`, error);
      toast({
        variant: "destructive",
        title: "Connection Error",
        description: `Failed to connect to suggestion feed for ${selectedPersona}`,
      });
      setSuggestionLoading(false);
    }

    return () => {
      if (socket) {
        socket.close();
      }
    }
  }, [selectedPersona, selectedDoc, toast]);

  // Request a suggestion from the server
  const requestSuggestion = () => {
    if (!suggestionSocketRef.current || suggestionSocketRef.current.readyState !== WebSocket.OPEN) {
      toast({
        variant: "destructive",
        title: "Connection Error",
        description: "WebSocket connection not available. Please try again.",
      });
      return;
    }
  
    setSuggestionLoading(true);
    
    // Single action to request the next suggestion
    suggestionSocketRef.current.send(JSON.stringify({ action: "get_suggestion" }));
  };

  const handlePersonaSelect = (persona: string) => {
    setSelectedPersona(prev => prev === persona ? null : persona);
    setSuggestions([]); // Clear previous suggestions when changing persona
  };

  const toggleEditMode = (suggestionId: string | number) => {
    setEditMode(prev => ({
      ...prev,
      [suggestionId]: !prev[suggestionId]
    }));
    
    // Initialize edited value with original replacement when entering edit mode
    if (!editMode[suggestionId]) {
      const suggestion = suggestions.find(s => s.id === suggestionId);
      if (suggestion) {
        setEditedReplacements(prev => ({
          ...prev,
          [suggestionId]: suggestion.replacement
        }));
      }
    }
  };

  const handleEditChange = (suggestionId: string | number, value: string) => {
    setEditedReplacements(prev => ({
      ...prev,
      [suggestionId]: value
    }));
  };

  const handleAcceptSuggestion = (suggestion: Suggestion) => {
    if (!suggestionSocketRef.current || suggestionSocketRef.current.readyState !== WebSocket.OPEN) {
      toast({
        variant: "destructive",
        title: "Connection Error",
        description: "WebSocket connection not available. Cannot accept suggestion.",
      });
      return;
    }

    // Get the possibly edited replacement
    const finalReplacement = editedReplacements[suggestion.id] || suggestion.replacement;
    
    // Create a complete suggestion object to send back
    const completeData = {
      action: "accept_suggestion",
      suggestion: {
        content: suggestion.content,
        replacement: finalReplacement,
        reason: suggestion.reason
      }
    };

    // Send complete suggestion data to backend
    suggestionSocketRef.current.send(JSON.stringify(completeData));

    // Keep UI responsive by immediately reflecting the change
    setSuggestions(prev => prev.filter(s => s.id !== suggestion.id));
    setDocumentContent(currentContent => 
      currentContent.replace(suggestion.content, finalReplacement)
    );
    
    toast({
      title: "Suggestion accepted",
      description: "The change has been applied to the document.",
    });
  };

  const handleRejectSuggestion = (suggestion: Suggestion) => {
    // Remove the suggestion from the list
    setSuggestions(prev => prev.filter(s => s.id !== suggestion.id));
    
    toast({
      title: "Suggestion rejected",
      description: "The suggestion has been dismissed.",
    });
  };

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Button
          variant={selectedDoc === 1 ? "default" : "outline"}
          onClick={() => setSelectedDoc(1)}
          disabled={loading}
        >
          View Doc 1
        </Button>
        <Button
          variant={selectedDoc === 2 ? "default" : "outline"}
          onClick={() => setSelectedDoc(2)}
          disabled={loading}
        >
          View Doc 2
        </Button>
      </div>

      <div className="flex flex-wrap gap-2 mb-4">
        {personasLoading ? (
          <Badge variant="outline" className="py-2">
            <Loader2 className="h-4 w-4 mr-1 animate-spin" />
            Loading personas...
          </Badge>
        ) : (
          personaList.map((persona) => (
            <Button
              key={persona}
              variant={selectedPersona === persona ? "default" : "outline"}
              onClick={() => handlePersonaSelect(persona)}
              className="text-sm"
            >
              {persona}
            </Button>
          ))
        )}
      </div>

      {selectedPersona && (
        <div className="mb-4">
          <Button 
            onClick={requestSuggestion} 
            disabled={suggestionLoading}
            className="flex items-center gap-2"
          >
            {suggestionLoading && <Loader2 className="h-4 w-4 animate-spin" />}
            Get Suggestion
          </Button>
        </div>
      )}

      <Card>
        <CardContent className="prose prose-invert max-w-none pt-6">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin" />
            </div>
          ) : (
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{documentContent}</ReactMarkdown>
          )}
        </CardContent>
      </Card>

      {selectedPersona && (
        <div className="mt-6">
          <h3 className="text-lg font-medium mb-4">Suggestions from {selectedPersona}</h3>
          
          {suggestionLoading && (
            <div className="flex items-center gap-2 text-muted-foreground py-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Loading suggestions...</span>
            </div>
          )}
          
          {suggestions.length === 0 && !suggestionLoading && (
            <div className="flex items-center gap-2 text-muted-foreground py-2">
              <AlertCircle className="h-4 w-4" />
              <span>No suggestions available. Click the button above to get suggestions.</span>
            </div>
          )}

          {suggestions.map((suggestion: Suggestion) => (
            <Card key={suggestion.id} className="mb-4">
              <CardContent className="pt-6">
                <div className="mb-4">
                  <h4 className="font-semibold mb-2">Reason for suggestion:</h4>
                  <p className="text-muted-foreground">{suggestion.reason}</p>
                </div>
                
                <div className="mb-4">
                  <h4 className="font-semibold mb-2">Proposed change:</h4>
                  {!editMode[suggestion.id] ? (
                    <div className="border rounded-md">
                      <ReactDiffViewer
                        oldValue={suggestion.content}
                        newValue={editedReplacements[suggestion.id] || suggestion.replacement}
                        splitView={false}
                        useDarkTheme={true}
                      />
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <div className="border rounded-md p-3 bg-muted text-muted-foreground">
                        <h5 className="text-sm font-medium mb-1">Original Text:</h5>
                        <div className="whitespace-pre-wrap">{suggestion.content}</div>
                      </div>
                      <div>
                        <h5 className="text-sm font-medium mb-1">Your Edit:</h5>
                        <Textarea 
                          value={editedReplacements[suggestion.id] || suggestion.replacement}
                          onChange={(e) => handleEditChange(suggestion.id, e.target.value)}
                          className="min-h-[100px]"
                        />
                      </div>
                    </div>
                  )}
                </div>
                
                <div className="flex gap-2 justify-end">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    onClick={() => handleRejectSuggestion(suggestion)}
                    className="flex items-center gap-1"
                  >
                    <XCircle className="h-4 w-4" />
                    Reject
                  </Button>
                  <Button 
                    variant="outline"
                    size="sm" 
                    onClick={() => toggleEditMode(suggestion.id)}
                    className="flex items-center gap-1"
                  >
                    <Edit className="h-4 w-4" />
                    {editMode[suggestion.id] ? "Preview" : "Edit"}
                  </Button>
                  <Button 
                    variant="default" 
                    size="sm" 
                    onClick={() => handleAcceptSuggestion(suggestion)}
                    className="flex items-center gap-1"
                  >
                    <CheckCircle className="h-4 w-4" />
                    Accept
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}

