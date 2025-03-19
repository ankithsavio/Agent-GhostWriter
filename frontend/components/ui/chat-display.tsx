import type React from "react"
import { User, BotIcon as Robot } from "lucide-react"

interface Message {
  role: string
  content: string
}

interface ChatDisplayProps {
  messages: Message[]
  iconA?: React.ReactNode
  iconB?: React.ReactNode
}

export function ChatDisplay({ messages, iconA = <User />, iconB = <Robot /> }: ChatDisplayProps) {
  const roles = Array.from(new Set(messages.map(m => m.role)));
  const isPrimaryRole = (role: string) => role === roles[0];
  
  const formatRoleName = (role: string) => 
    role.charAt(0).toUpperCase() + role.slice(1);

  return (
    <div className="space-y-4">
      {messages.map((message, index) => {
        const isPrimary = isPrimaryRole(message.role);
        
        return (
          <div key={index} className={`flex ${isPrimary ? "justify-end" : "justify-start"}`}>
            <div
              className={`flex items-start space-x-2 rounded-lg px-4 py-2 max-w-[80%] ${
                isPrimary
                  ? "bg-primary text-primary-foreground flex-row-reverse"
                  : "bg-muted text-muted-foreground"
              }`}
            >
              <div className={`flex-shrink-0 mt-1 ${isPrimary ? "ml-3" : "mr-3"}`}>
                {isPrimary ? iconA : iconB}
              </div>
              <div>
                <div className="text-xs font-medium mb-1">{formatRoleName(message.role)}</div>
                <div>{message.content}</div>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  )
}

