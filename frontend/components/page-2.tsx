"use client"

import { useState, useEffect } from "react"
import ReactMarkdown from "react-markdown"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { applyFunction, initializeSocket, getAvailableFunctions, getDocumentContent } from "@/lib/api"
import type { Socket } from "socket.io-client"

export function Page2() {
  const [selectedDoc, setSelectedDoc] = useState<"Doc1" | "Doc2">("Doc1")
  const [markdown, setMarkdown] = useState({
    Doc1: "",
    Doc2: "",
  })
  const [functions, setFunctions] = useState<string[]>([])
  const [socket, setSocket] = useState<Socket | null>(null)

  useEffect(() => {
    const newSocket = initializeSocket()
    setSocket(newSocket)

    newSocket.on("document_update", (data: { docType: string; content: string }) => {
      setMarkdown((prev) => ({
        ...prev,
        [data.docType]: data.content,
      }))
    })

    getAvailableFunctions().then(setFunctions).catch(console.error)

    getDocumentContent("Doc1")
      .then((content) => {
        setMarkdown((prev) => ({ ...prev, Doc1: content }))
      })
      .catch(console.error)
    getDocumentContent("Doc2")
      .then((content) => {
        setMarkdown((prev) => ({ ...prev, Doc2: content }))
      })
      .catch(console.error)

    return () => {
      newSocket.disconnect()
    }
  }, [])

  const handleFunctionClick = async (functionName: string) => {
    try {
      await applyFunction(functionName, markdown[selectedDoc], selectedDoc)
    } catch (error) {
      console.error("Function application failed:", error)
    }
  }

  return (
    <div className="grid gap-6 md:grid-cols-[1fr_auto]">
      <div className="space-y-4">
        <div className="flex gap-2">
          <Button variant={selectedDoc === "Doc1" ? "default" : "outline"} onClick={() => setSelectedDoc("Doc1")}>
            View Doc 1
          </Button>
          <Button variant={selectedDoc === "Doc2" ? "default" : "outline"} onClick={() => setSelectedDoc("Doc2")}>
            View Doc 2
          </Button>
        </div>
        <Card>
          <CardContent className="prose prose-invert max-w-none pt-6">
            <ReactMarkdown>{markdown[selectedDoc]}</ReactMarkdown>
          </CardContent>
        </Card>
      </div>
      <div className="flex flex-col gap-2">
        {functions.map((func) => (
          <Button key={func} variant="outline" onClick={() => handleFunctionClick(func)}>
            Apply {func}
          </Button>
        ))}
      </div>
    </div>
  )
}

