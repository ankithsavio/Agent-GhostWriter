import { Menu, RefreshCw } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"

interface SidebarProps {
  currentPage: "page1" | "page2" | "page3" 
  onPageChange: (page: "page1" | "page2" | "page3") => void
  onRestart: () => void
  isRestarting?: boolean
}

export function Sidebar({ currentPage, onPageChange, onRestart, isRestarting = false }: SidebarProps) {
  const buttons = [
    { id: "page1", label: "Upload" },
    { id: "page2", label: "Edit" },
    { id: "page3", label: "Research Doc" },
  ]

  return (
    <>
      {/* Mobile Sidebar */}
      <Sheet>
        <SheetTrigger asChild>
          <Button variant="ghost" size="icon" className="md:hidden">
            <Menu className="h-6 w-6" />
          </Button>
        </SheetTrigger>
        <SheetContent side="left" className="w-64 p-0">
          <nav className="flex flex-col gap-2 p-4">
            {buttons.map((button) => (
              <Button
                key={button.id}
                variant={currentPage === button.id ? "default" : "ghost"}
                className="w-full justify-start"
                onClick={() => onPageChange(button.id as "page1" | "page2" | "page3")}
              >
                {button.label}
              </Button>
            ))}
            
            {/* Restart Button for Mobile */}
            <div className="mt-auto pt-4">
              <Button 
                variant="destructive" 
                className="w-full justify-start" 
                onClick={onRestart}
                disabled={isRestarting}
              >
                <RefreshCw className="mr-2 h-4 w-4" />
                {isRestarting ? "Restarting..." : "Restart"}
              </Button>
            </div>
          </nav>
        </SheetContent>
      </Sheet>

      {/* Desktop Sidebar */}
      <nav className="hidden w-64 border-r bg-card p-4 md:block flex flex-col">
        <div className="flex flex-col gap-2">
          {buttons.map((button) => (
            <Button
              key={button.id}
              variant={currentPage === button.id ? "default" : "ghost"}
              className="w-full justify-start"
              onClick={() => onPageChange(button.id as "page1" | "page2" | "page3")}
            >
              {button.label}
            </Button>
          ))}
        </div>
        
        {/* Restart Button for Desktop */}
        <div className="mt-auto pt-4">
          <Button 
            variant="destructive" 
            className="w-full justify-start" 
            onClick={onRestart}
            disabled={isRestarting}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            {isRestarting ? "Restarting..." : "Restart"}
          </Button>
        </div>
      </nav>
    </>
  )
}

