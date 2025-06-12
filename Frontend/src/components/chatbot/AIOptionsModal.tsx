import React, { useState, useEffect, useRef } from "react";
import { useWebSocket } from "@/contexts/websocket-provider";
import { Button } from "@/components/ui/button";
import { Todo } from "@/components/todo/types-todo";
import { Habit } from "@/components/todo/types-habit";

interface AIOption {
  id: string;
  title: string;
  description: string;
}

type TargetDataType = Todo | Habit | Record<string, unknown>;

interface AIOptionsModalProps {
  targetType: "todo" | "habit" | "event" | "note";
  targetId: string;
  targetData: TargetDataType;
  onClose: () => void;
}

export const AIOptionsModal: React.FC<AIOptionsModalProps> = ({
  targetType,
  targetId,
  targetData,
  onClose,
}) => {
  const [options, setOptions] = useState<AIOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedOption, setSelectedOption] = useState<string | null>(null);
  const [processing, setProcessing] = useState(false);
  const [result, setResult] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [requestSent, setRequestSent] = useState(false);
  const [requestTimeout, setRequestTimeout] = useState<NodeJS.Timeout | null>(
    null
  );
  const requestAttempts = useRef(0);
  const maxRequestAttempts = 3;

  const { sendMessage, isConnected } = useWebSocket();

  // Add a timeout to handle cases where no response is received
  useEffect(() => {
    if (loading && requestSent) {
      const timeout = setTimeout(() => {
        setLoading(false);
        setError("Request timed out. Please try again later.");
      }, 15000); // 15 seconds timeout (increased from 10)

      setRequestTimeout(timeout);

      return () => {
        if (timeout) clearTimeout(timeout);
      };
    }
  }, [loading, requestSent]);

  // Handle connection state changes and request sending
  useEffect(() => {
    // Only send request if not already sent and connection is established
    if (
      isConnected &&
      sendMessage &&
      !requestSent &&
      requestAttempts.current < maxRequestAttempts
    ) {
      const sendRequest = () => {
        try {
          console.log(
            `Sending AI options request for ${targetType} ${targetId}`
          );

          // Enhanced logging for debugging
          console.log("Target data:", targetData);

          const success = sendMessage({
            type: "ai_options_request",
            target_type: targetType,
            target_id: targetId,
            target_data: targetData,
          });

          if (success === true) {
            setRequestSent(true);
            requestAttempts.current += 1;
          } else {
            // If sendMessage returns false, the connection was lost
            setTimeout(sendRequest, 1000); // Try again in 1 second
          }
        } catch (err) {
          console.error("Error sending WebSocket message:", err);
          setError("Error connecting to AI service. Please try again later.");
          setLoading(false);
        }
      };

      // Start sending the request
      sendRequest();
    } else if (!isConnected && requestAttempts.current >= maxRequestAttempts) {
      // Give up after max attempts
      console.error("WebSocket not connected after multiple attempts");
      setError("Could not connect to AI service. Please try again later.");
      setLoading(false);
    } else if (!isConnected) {
      // Not connected yet, but don't give up
      console.warn("WebSocket not connected, waiting...");
    }
  }, [isConnected, sendMessage, targetType, targetId, targetData, requestSent]);

  // Listen for AI options response from WebSocket
  useEffect(() => {
    const handleAIOptionsResponse = (
      e: CustomEvent<{
        type: string;
        data: {
          targetId: string;
          targetType: string;
          options?: AIOption[];
          error?: string;
          result?: string;
          optionId?: string;
          success?: boolean;
        };
      }>
    ) => {
      console.log("Received AI event:", e.detail?.type);

      if (
        e.detail?.type === "ai_options_response" &&
        e.detail?.data?.targetId === targetId
      ) {
        // Clear timeout if it exists
        if (requestTimeout) {
          clearTimeout(requestTimeout);
          setRequestTimeout(null);
        }

        // Check if there was an error or if success is explicitly false
        if (e.detail?.data?.error || e.detail?.data?.success === false) {
          setError(e.detail.data.error || "Failed to get AI options");
          setLoading(false);
          return;
        }

        setOptions(e.detail.data.options || []);
        setLoading(false);
      }

      if (
        e.detail?.type === "ai_option_processing" &&
        e.detail?.data?.targetId === targetId
      ) {
        // Handle processing notification - this is sent while the AI is working
        setProcessing(true);
        setError(null);
      }

      if (
        e.detail?.type === "ai_option_result" &&
        e.detail?.data?.targetId === targetId
      ) {
        // Check for explicit success/failure flag first
        if (e.detail?.data?.success === false) {
          setError(
            e.detail.data.error || "An error occurred processing the request"
          );
          setProcessing(false);
          return;
        }

        // Also check for traditional error field
        if (e.detail?.data?.error) {
          setError(e.detail.data.error || "Unknown error");
          setProcessing(false);
          return;
        }

        // Format the result properly - atomic agents may return structured output
        const resultContent = e.detail.data.result || null;
        setResult(
          typeof resultContent === "string"
            ? resultContent
            : JSON.stringify(resultContent, null, 2)
        );
        setProcessing(false);
      }
    };

    window.addEventListener(
      "websocket_ai_event",
      handleAIOptionsResponse as EventListener
    );

    return () => {
      window.removeEventListener(
        "websocket_ai_event",
        handleAIOptionsResponse as EventListener
      );
    };
  }, [targetId, requestTimeout]);

  const handleOptionSelect = (optionId: string) => {
    setSelectedOption(optionId);
    setProcessing(true);
    setError(null);
    setResult(null); // Clear any previous results

    // Request AI to process the selected option
    if (isConnected && sendMessage) {
      const success = sendMessage({
        type: "ai_process_request",
        option_id: optionId,
        target_type: targetType,
        target_id: targetId,
        target_data: targetData,
      });

      if (success !== true) {
        setError("Could not connect to AI service. Please try again later.");
        setProcessing(false);
      }
    } else {
      setError("Could not connect to AI service. Please try again later.");
      setProcessing(false);
    }
  };

  // Return to options view if there's an error during processing
  const handleRetry = () => {
    setError(null);
    setProcessing(false);
    setResult(null);
    if (loading) {
      // If we're still in the loading state, retry the request
      setRequestSent(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-background rounded-lg shadow-lg w-full max-w-md p-6">
        <h3 className="text-lg font-medium mb-4">AI Assistant Options</h3>

        {loading ? (
          <div className="py-10 text-center">
            <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary mx-auto"></div>
            <p className="mt-4 text-muted-foreground">
              Analyzing {targetType}...
            </p>
          </div>
        ) : error ? (
          <div className="py-4">
            <div
              className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative"
              role="alert"
            >
              <strong className="font-bold">Error: </strong>
              <span className="block sm:inline">{error}</span>
            </div>
            <div className="mt-4 flex justify-between">
              <Button variant="outline" onClick={handleRetry}>
                Retry
              </Button>
              <Button onClick={onClose}>Close</Button>
            </div>
          </div>
        ) : result ? (
          <div className="py-4">
            <div className="bg-muted p-4 rounded-md text-sm whitespace-pre-wrap">
              {result}
            </div>
            <div className="mt-4 flex justify-end">
              <Button onClick={onClose}>Close</Button>
            </div>
          </div>
        ) : options.length === 0 ? (
          <div className="py-4">
            <div
              className="bg-yellow-100 border border-yellow-400 text-yellow-700 px-4 py-3 rounded relative"
              role="alert"
            >
              <span className="block sm:inline">
                No AI options available for this item.
              </span>
            </div>
            <div className="mt-4 flex justify-end">
              <Button onClick={onClose}>Close</Button>
            </div>
          </div>
        ) : (
          <>
            <div className="space-y-3 max-h-80 overflow-y-auto">
              {options.map((option) => (
                <div
                  key={option.id}
                  className={`p-3 rounded-md border cursor-pointer hover:bg-accent transition-colors
                    ${
                      selectedOption === option.id
                        ? "border-primary bg-accent"
                        : "border-border"
                    }`}
                  onClick={() => handleOptionSelect(option.id)}
                >
                  <h4 className="font-medium">{option.title}</h4>
                  <p className="text-sm text-muted-foreground">
                    {option.description}
                  </p>
                </div>
              ))}
            </div>

            <div className="mt-4 flex justify-end gap-2">
              <Button variant="outline" onClick={onClose}>
                Cancel
              </Button>
              <Button
                disabled={!selectedOption || processing}
                onClick={() =>
                  selectedOption && handleOptionSelect(selectedOption)
                }
              >
                {processing ? (
                  <div className="flex items-center">
                    <div className="animate-spin mr-2 h-4 w-4 border-b-2 border-white rounded-full"></div>
                    Processing...
                  </div>
                ) : (
                  "Process"
                )}
              </Button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};
