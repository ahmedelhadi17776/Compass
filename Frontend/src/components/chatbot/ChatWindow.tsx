import React, { useRef, useEffect, useState } from 'react';
import { Message, Position } from './types';
import { useTheme } from '@/contexts/theme-provider';

interface ChatWindowProps {
  messages: Message[];
  inputText: string;
  setInputText: React.Dispatch<React.SetStateAction<string>>;
  handleSendMessage: () => void;
  toggleChat: () => void;
  isFullPage: boolean;
  toggleFullPage: () => void;
  position: Position;
  setPosition: React.Dispatch<React.SetStateAction<Position>>;
  isClosing: boolean;
  isOpening: boolean;
}

const ChatWindow: React.FC<ChatWindowProps> = ({
  messages,
  inputText,
  setInputText,
  handleSendMessage,
  toggleChat,
  isFullPage,
  toggleFullPage,
  position,
  setPosition,
  isClosing,
  isOpening,
}) => {
  const chatWindowRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { theme } = useTheme();
  const isDarkTheme = theme === 'dark';
  const [hasInitializedAnimation, setHasInitializedAnimation] = useState(false);

  // Initialize animation state
  useEffect(() => {
    // Set a very short timeout to trigger the animation
    if (!hasInitializedAnimation) {
      // Force an initial state for the animation
      setTimeout(() => {
        setHasInitializedAnimation(true);
      }, 10);
    }
  }, [hasInitializedAnimation]);

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Simple drag functionality
  const [isDragging, setIsDragging] = React.useState(false);
  const [dragStart, setDragStart] = React.useState({ x: 0, y: 0 });

  const handleMouseDown = (e: React.MouseEvent) => {
    if (isFullPage) return;
    setIsDragging(true);
    setDragStart({ x: e.clientX - position.x, y: e.clientY - position.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDragging) return;
    setPosition({
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    });
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener('mouseup', handleMouseUp);
      document.addEventListener('mousemove', handleMouseMove as any);
    } else {
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('mousemove', handleMouseMove as any);
    }
    return () => {
      document.removeEventListener('mouseup', handleMouseUp);
      document.removeEventListener('mousemove', handleMouseMove as any);
    };
  }, [isDragging]);

  // Determine the current animation state
  const getAnimationStyles = () => {
    if (isClosing) {
      return {
        opacity: 0,
        scale: 0.95
      };
    } else if (isOpening || !hasInitializedAnimation) {
      return {
        opacity: hasInitializedAnimation ? 1 : 0,
        scale: hasInitializedAnimation ? 1 : 0.95
      };
    } else {
      return {
        opacity: 1,
        scale: 1
      };
    }
  };

  const { opacity, scale } = getAnimationStyles();

  return (
    <div
      ref={chatWindowRef}
      style={{
        position: 'fixed',
        top: isFullPage ? 0 : undefined,
        left: isFullPage ? 0 : undefined,
        right: isFullPage ? 0 : undefined,
        bottom: isFullPage ? 0 : undefined,
        width: isFullPage ? '100%' : '350px',
        height: isFullPage ? '100%' : '500px',
        transform: isFullPage 
          ? 'none' 
          : `translate(${position.x}px, ${position.y}px) scale(${scale})`,
        borderRadius: isFullPage ? '0' : '12px',
        overflow: 'hidden',
        zIndex: 40,
        boxShadow: '0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
        transition: 'width 0.2s ease, height 0.2s ease, border-radius 0.2s ease, opacity 0.3s ease, transform 0.3s ease',
        opacity: opacity,
      }}
      className={`${
        !isFullPage && 'bottom-6 right-6'
      } ${isDarkTheme ? 'bg-[#202020] text-[#e5e5e5]' : 'bg-white text-gray-800'} flex flex-col border-b-[2px] border-[#E7E7E7]`}
    >
      {/* Chat header */}
      <div 
        className={`${isDarkTheme ? 'bg-[#202020]' : 'bg-white'} shadow-sm p-4 flex justify-between items-center`}
        onMouseDown={handleMouseDown}
        style={{ cursor: isFullPage ? 'default' : 'move' }}
      >
        <h1 className={`text-lg font-medium ${isDarkTheme ? 'text-[#e5e5e5]' : 'text-gray-800'}`}>AI Assistant</h1>
        <div className="flex space-x-2">
          <button
            onClick={toggleFullPage}
            className={`p-1.5 rounded-md ${isDarkTheme ? 'hover:bg-[#3b3b3b]' : 'hover:bg-gray-100'} transition-colors`}
            aria-label={isFullPage ? "Minimize chat" : "Expand chat"}
            tabIndex={0}
          >
            {isFullPage ? (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-4 w-4 text-[#E7E7E7]"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5"
                />
              </svg>
            ) : (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                className="h-4 w-4 text-[#E7E7E7]"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5v-4m0 4h-4m4 0l-5-5"
                />
              </svg>
            )}
          </button>
          <button
            onClick={toggleChat}
            className={`p-1.5 rounded-md ${isDarkTheme ? 'hover:bg-[#3b3b3b]' : 'hover:bg-gray-100'} transition-colors`}
            aria-label="Close chat"
            tabIndex={0}
          >
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-4 w-4 text-[#E7E7E7]"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Messages container */}
      <div className={`flex-1 overflow-y-auto p-4 space-y-3 ${isDarkTheme ? 'bg-[#202020]' : 'bg-white'}`}>
        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${
              message.sender === 'user' ? 'justify-end' : 'justify-start'
            }`}
          >
            <div
              className={`max-w-[70%] rounded-lg p-2.5 ${
                message.sender === 'user'
                  ? 'bg-blue-500 text-white'
                  : isDarkTheme 
                    ? 'bg-[#3b3b3b] text-[#e5e5e5]' 
                    : 'bg-gray-100 text-gray-800'
              }`}
            >
              <p className="text-sm">{message.text}</p>
              <span className="text-xs opacity-75 mt-1 inline-block">
                {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
          </div>
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input area */}
      <div className={`${isDarkTheme ? 'bg-[#202020]' : 'bg-white'} p-3 shadow-sm border-t ${isDarkTheme ? 'border-[#3b3b3b]' : 'border-gray-200'}`}>
        <div className="flex space-x-2 rounded-[15px]">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
            placeholder="Type your message..."
            className={`flex-1 p-2 text-sm border ${
              isDarkTheme 
                ? 'bg-[#262626] border-[#3b3b3b] text-white placeholder-gray-500 focus:border-blue-400' 
                : 'bg-white border-gray-300 text-gray-800 focus:border-blue-500'
            } rounded-[15px] focus:outline-none`}
            aria-label="Message input"
            tabIndex={0}
          />
          <button
            onClick={handleSendMessage}
            className="px-3 py-2 bg-white-500 text-white text-sm rounded-md hover:bg-white-600 transition-colors focus:outline-none focus:ring-2 focus:ring-white-300"
            aria-label="Send message"
            tabIndex={0} 
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
};

export default ChatWindow;