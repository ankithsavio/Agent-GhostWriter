"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Tabs, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent } from "@/components/ui/card"
import { uploadFile, processText, initializeSocket, getProgressStages } from "@/lib/api"
import type { Socket } from "socket.io-client"

export function Page1() {
  const [text, setText] = useState("")
  const [files, setFiles] = useState({ doc1: "", doc2: "" })
  const [progressStages, setProgressStages] = useState<string[]>([])
  const [currentStage, setCurrentStage] = useState("")
  const [socket, setSocket] = useState<Socket | null>(null)

  useEffect(() => {
    const newSocket = initializeSocket()
    setSocket(newSocket)

    newSocket.on("processing_update", (data: { stage: string; message: string }) => {
      setCurrentStage(data.stage)
    })

    getProgressStages()
      .then((stages) => {
        setProgressStages(stages)
        if (stages.length > 0) {
          setCurrentStage(stages[0])
        }
      })
      .catch((error) => {
        console.error("Failed to fetch progress stages:", error)
      })

    return () => {
      newSocket.disconnect()
    }
  }, [])

  const handleFileUpload = (docNumber: 1 | 2) => async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      try {
        const result = await uploadFile(file, `doc${docNumber}`)
        setFiles((prev) => ({
          ...prev,
          [`doc${docNumber}`]: result.filename,
        }))
      } catch (error) {
        console.error("File upload failed:", error)
      }
    }
  }

  const handleProcessText = async () => {
    if (text.trim()) {
      try {
        await processText(text)
      } catch (error) {
        console.error("Text processing failed:", error)
      }
    }
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="grid gap-6 md:grid-cols-[2fr_1fr]">
        <div className="space-y-4">
          <h2 className="text-lg font-semibold">Enter Text</h2>
          <Textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            className="min-h-[200px]"
            placeholder="Enter your text here..."
          />
          <Button onClick={handleProcessText}>Process Text</Button>
        </div>
        <div className="space-y-4">
          <div className="space-y-2">
            <h2 className="text-lg font-semibold">Upload Documents</h2>
            <div className="grid gap-4">
              {[1, 2].map((docNumber) => (
                <div key={docNumber}>
                  <input
                    type="file"
                    id={`doc${docNumber}`}
                    className="hidden"
                    onChange={handleFileUpload(docNumber as 1 | 2)}
                  />
                  <Button
                    variant="outline"
                    className="w-full"
                    onClick={() => document.getElementById(`doc${docNumber}`)?.click()}
                  >
                    Upload Doc {docNumber}
                  </Button>
                  {files[`doc${docNumber}` as "doc1" | "doc2"] && (
                    <p className="mt-2 text-sm text-muted-foreground">{files[`doc${docNumber}` as "doc1" | "doc2"]}</p>
                  )}
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <Card>
        <CardContent className="pt-6">
          <Tabs value={currentStage} onValueChange={setCurrentStage}>
            <TabsList className="w-full justify-start">
              {progressStages.map((stage) => (
                <TabsTrigger key={stage} value={stage} className="flex-1">
                  {stage}
                </TabsTrigger>
              ))}
            </TabsList>
          </Tabs>
          <div className="mt-4 p-4">
            <p className="text-muted-foreground">Current Stage: {currentStage}</p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

