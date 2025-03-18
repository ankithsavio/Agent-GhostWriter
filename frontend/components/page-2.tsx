"use client"

import { useState, useEffect, useRef } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import remarkBreaks from 'remark-breaks'
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Loader2, RefreshCw } from "lucide-react"
import { useToast } from "@/components/ui/use-toast"
import * as api from "@/lib/api"

type ReportType = "resume" | "cover_letter"

export function Page2() {
  const { toast } = useToast()
  const [selectedReport, setSelectedReport] = useState<ReportType>("resume")
  const [reportContent, setReportContent] = useState("")
  const [loading, setLoading] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  const abortControllerRef = useRef<AbortController | null>(null)

  const fetchReport = async (reportType: ReportType) => {
    // Abort any existing request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
    }
    
    // Create new abort controller for this request
    abortControllerRef.current = new AbortController()
    
    setLoading(true)
    setIsProcessing(false)
    
    try {
      const fetchFunction = reportType === "resume" 
        ? api.fetchResumeReport 
        : api.fetchCoverLetterReport;
      
      const data = await fetchFunction(abortControllerRef.current.signal);
      
      // Check if report is still processing
      if (data.processing) {
        setIsProcessing(true);
        toast({
          title: "Report is being generated",
          description: "The report is not ready yet. You can click refresh to check again."
        });
        return;
      }
      
      setReportContent(data.content || "No content available");
    } catch (error) {
      // Only show error if it's not an abort error
      if (error instanceof Error && error.name !== 'AbortError') {
        console.error(`Failed to fetch ${reportType} report:`, error);
        toast({
          variant: "destructive",
          title: "Error",
          description: error instanceof Error ? error.message : "Failed to fetch report",
        });
      }
    } finally {
      setLoading(false);
      abortControllerRef.current = null;
    }
  }

  // Fetch the initial report
  useEffect(() => {
    fetchReport(selectedReport);
    
    // Cleanup function to cancel any pending fetches
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    }
  }, [selectedReport]);

  const handleReportChange = (reportType: ReportType) => {
    if (reportType !== selectedReport) {
      setSelectedReport(reportType);
      setReportContent("");
    }
  }

  const handleRefresh = () => {
    fetchReport(selectedReport);
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between">
        <div className="flex gap-2">
          <Button
            variant={selectedReport === "resume" ? "default" : "outline"}
            onClick={() => handleReportChange("resume")}
            disabled={loading}
          >
            Resume Report
          </Button>
          <Button
            variant={selectedReport === "cover_letter" ? "default" : "outline"}
            onClick={() => handleReportChange("cover_letter")}
            disabled={loading}
          >
            Cover Letter Report
          </Button>
        </div>
        
        <Button 
          variant="outline" 
          onClick={handleRefresh} 
          disabled={loading}
        >
          {loading ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          <span className="ml-2">Refresh</span>
        </Button>
      </div>

      <Card>
        <CardContent className="prose prose-invert max-w-none pt-6">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-8 gap-2">
              <Loader2 className="h-8 w-8 animate-spin" />
              <p className="text-muted-foreground">Loading report...</p>
            </div>
          ) : isProcessing ? (
            <div className="flex flex-col items-center justify-center py-8 gap-2">
              <p className="text-muted-foreground">Your report is being generated.</p>
              <p className="text-muted-foreground">Click refresh to check if it's ready.</p>
            </div>
          ) : reportContent ? (
            <ReactMarkdown remarkPlugins={[remarkGfm, remarkBreaks]}>{reportContent}</ReactMarkdown>
          ) : (
            <p className="text-muted-foreground text-center py-8">No report content available</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

