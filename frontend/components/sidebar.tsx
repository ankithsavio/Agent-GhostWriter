import { Menu } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"

interface SidebarProps {
  currentPage: "page1" | "page2" | "page3" | "page4"
  onPageChange: (page: "page1" | "page2" | "page3" | "page4") => void
}

export function Sidebar({ currentPage, onPageChange }: SidebarProps) {
  const buttons = [
    { id: "page1", label: "Upload" },
    { id: "page2", label: "Edit" },
    { id: "page3", label: "Research Doc" },
    { id: "page4", label: "Logs" },
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
                onClick={() => onPageChange(button.id as "page1" | "page2" | "page3" | "page4")}
              >
                {button.label}
              </Button>
            ))}
          </nav>
        </SheetContent>
      </Sheet>

      {/* Desktop Sidebar */}
      <nav className="hidden w-64 border-r bg-card p-4 md:block">
        <div className="flex flex-col gap-2">
          {buttons.map((button) => (
            <Button
              key={button.id}
              variant={currentPage === button.id ? "default" : "ghost"}
              className="w-full justify-start"
              onClick={() => onPageChange(button.id as "page1" | "page2" | "page3" | "page4")}
              >
                {button.label}
              </Button>
            ))}
        </div>
      </nav>
    </>
  )
}

