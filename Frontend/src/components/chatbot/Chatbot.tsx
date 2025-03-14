import React, { useState, useEffect } from 'react';
import ChatbotIcon from './ChatbotIcon';
import ChatWindow from './ChatWindow';
import { Message, Position } from './types';

const Chatbot: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([
    {
      text: 'Hello! How can I help you today?',
      sender: 'bot',
      timestamp: new Date(),
    },
  ]);
  const [inputText, setInputText] = useState('');
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [isClosing, setIsClosing] = useState(false);
  const [isOpening, setIsOpening] = useState(false);
  const [isFullPage, setIsFullPage] = useState(false);
  const [position, setPosition] = useState<Position>({ x: 0, y: 0 });

  const handleSendMessage = async () => {
    if (!inputText.trim()) return;

    const userMessage: Message = {
      text: inputText,
      sender: 'user',
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInputText('');

    // TODO: Integrate with a chatbot API
    const botMessage: Message = {
      text: 'I understand your message. This is a placeholder response.',
      sender: 'bot',
      timestamp: new Date(),
    };

    setTimeout(() => {
      setMessages((prev) => [...prev, botMessage]);
    }, 1000);
  };

  const toggleChat = () => {
    if (isChatOpen) {
      // Start closing animation
      setIsClosing(true);
      // Wait for animation to complete before removing from DOM
      setTimeout(() => {
        setIsChatOpen(false);
        setIsClosing(false);
      }, 300); // Match this with the CSS transition duration
    } else {
      // Start opening animation
      setIsOpening(true);
      setIsChatOpen(true);
      // Reset opening state after animation completes
      setTimeout(() => {
        setIsOpening(false);
      }, 300);
    }
  };

  // This function is kept for compatibility but will be replaced by navigation to AI Assistant
  const toggleFullPage = () => {
    setIsFullPage(!isFullPage);
  };

  return (
    <>
      <ChatbotIcon toggleChat={toggleChat} isChatOpen={isChatOpen} />
      {(isChatOpen || isClosing) && (
        <ChatWindow
          messages={messages}
          inputText={inputText}
          setInputText={setInputText}
          handleSendMessage={handleSendMessage}
          toggleChat={toggleChat}
          isFullPage={isFullPage}
          toggleFullPage={toggleFullPage}
          position={position}
          setPosition={setPosition}
          isClosing={isClosing}
          isOpening={isOpening}
          onClose={toggleChat}
        />
      )}
    </>
  );
};

export default Chatbot;
