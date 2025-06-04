import React, { useState, useEffect } from 'react';
import { useTheme } from '@/contexts/theme-provider';
import { Eye } from 'lucide-react';

interface ChatbotIconProps {
  toggleChat: () => void;
  isChatOpen: boolean;
}

const ChatbotIcon: React.FC<ChatbotIconProps> = ({ toggleChat, isChatOpen }) => {
  const [isHovered, setIsHovered] = useState(false);
  const [showTooltip, setShowTooltip] = useState(false);
  const { theme } = useTheme();
  const isDarkTheme = theme === 'dark';

  useEffect(() => {
    let timeoutId: NodeJS.Timeout;
    if (isHovered && !isChatOpen) {
      timeoutId = setTimeout(() => setShowTooltip(true), 500);
    } else {
      setShowTooltip(false);
    }
    return () => clearTimeout(timeoutId);
  }, [isHovered, isChatOpen]);

  return (
    <div className="fixed bottom-6 right-6 z-50">
      <button
        onClick={toggleChat}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className="w-12 h-12 bg-[#2a2a2a] text-[#e5e5e5] rounded-full shadow-md hover:shadow-lg hover:bg-[#3b3b3b] transition-all flex items-center justify-center focus:outline-none border-b-[2px] border-[#E7E7E7]"
        aria-label="Open chat"
        tabIndex={0}
      >
        <Eye className="h-5 w-5 text-[#E7E7E7]" />
      </button>
      
      {/* Simple tooltip with fade animation */}
      <div 
        className={`absolute bottom-16 right-0 ${
          isDarkTheme 
            ? 'bg-[#2a2a2a] text-[#e5e5e5]' 
            : 'bg-white text-gray-800'
        } px-3 py-1.5 rounded-md shadow-md text-sm whitespace-nowrap transition-opacity duration-200 ${
          showTooltip ? 'opacity-100' : 'opacity-0'
        }`}
      >
        Chat with IRIS, our AI assistant
      </div>
    </div>
  );
};

export default ChatbotIcon;