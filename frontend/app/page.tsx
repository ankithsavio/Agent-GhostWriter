"use client"

import { useState } from "react"
import { Sidebar } from "@/components/sidebar"
import { Page1 } from "@/components/page-1"
import { Page2 } from "@/components/page-2"

export default function Home() {
  const [currentPage, setCurrentPage] = useState<"page1" | "page2">("page1")

  return (
    <div className="flex h-screen bg-background">
      <Sidebar currentPage={currentPage} onPageChange={setCurrentPage} />
      <main className="flex-1 overflow-auto p-6">{currentPage === "page1" ? <Page1 /> : <Page2 />}</main>
    </div>
  )
}

