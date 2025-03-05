"use client"

import { useState, useEffect } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import { Card, CardContent } from "@/components/ui/card"
import { Loader2 } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import * as api from "@/lib/api"

export function Page3() {
  const { toast } = useToast()
  const [documentContent, setDocumentContent] = useState("")
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchResearchDocument()
  }, [])

  async function fetchResearchDocument() {
    try {
      setLoading(true)
      const data = await api.fetchResearchDocument()
      setDocumentContent(data.content)
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to fetch research document",
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">Research Document</h2>
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
    </div>
  )
}

