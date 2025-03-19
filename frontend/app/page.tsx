"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { Page1 } from "@/components/page-1"
import { Page2 } from "@/components/page-2"
import { Page3 } from "@/components/page-3"
import { useToast } from "@/components/ui/use-toast"

const API_BASE_URL = "http://localhost:8080"

export default function Home() {
  const [currentPage, setCurrentPage] = useState<"page1" | "page2" | "page3">("page1")
  const [isRestarting, setIsRestarting] = useState(false)
  const [refreshKey, setRefreshKey] = useState(0) // Use to force re-render of child components
  const { toast } = useToast()

  const handleRestart = async () => {
    try {
      setIsRestarting(true)
      
      const response = await fetch(`${API_BASE_URL}/restart`, {
        method: 'POST',
      })
      
      if (!response.ok) {
        throw new Error('Failed to restart the application')
      }
      
      // Show success toast
      toast({
        title: "Success",
        description: "Application restarted successfully",
      })
      
      // Force re-render of child components to reset their state
      setRefreshKey(prev => prev + 1)
      
    } catch (error) {
      toast({
        variant: "destructive",
        title: "Error",
        description: error instanceof Error ? error.message : "Failed to restart the application",
      })
    } finally {
      setIsRestarting(false)
    }
  }

  return (
    <div className="flex h-screen bg-background">
      <Sidebar 
        currentPage={currentPage} 
        onPageChange={setCurrentPage} 
        onRestart={handleRestart}
        isRestarting={isRestarting}
      />
      <main className="flex-1 overflow-auto p-6">
        {/* Use key to force re-render of components when restart happens */}
        {currentPage === "page1" ? <Page1 key={`page1-${refreshKey}`} /> : 
         currentPage === "page2" ? <Page2 key={`page2-${refreshKey}`} /> : 
         <Page3 key={`page3-${refreshKey}`} />}
      </main>
    </div>
  )
}

