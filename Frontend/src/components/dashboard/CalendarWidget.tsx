import React from 'react';

type Event = {
  id: string;
  title: string;
  startTime: string;
  endTime: string;
  date: Date;
  isPurple?: boolean;
};

type Day = {
  date: Date;
  dayOfWeek: string;
  dayOfMonth: number;
  events: Event[];
};

const CalendarWidget: React.FC = () => {
  // Sample data to match the image
  const currentMonth = "March";
  const days: Day[] = [
    {
      date: new Date(2023, 2, 20),
      dayOfWeek: "Mo",
      dayOfMonth: 20,
      events: []
    },
    {
      date: new Date(2023, 2, 21),
      dayOfWeek: "Tu",
      dayOfMonth: 21,
      events: [
        {
          id: "1",
          title: "Project Onboarding Meeting",
          startTime: "09:15",
          endTime: "10:15 AM",
          date: new Date(2023, 2, 21),
          isPurple: true
        },
        {
          id: "2",
          title: "Dinner Meeting with Client",
          startTime: "06:30",
          endTime: "08:00 PM",
          date: new Date(2023, 2, 21),
          isPurple: true
        }
      ]
    },
    {
      date: new Date(2023, 2, 25),
      dayOfWeek: "Sa",
      dayOfMonth: 25,
      events: [
        {
          id: "3",
          title: "Coffee Date",
          startTime: "02:30",
          endTime: "03:30 PM",
          date: new Date(2023, 2, 25),
          isPurple: false
        }
      ]
    }
  ];

  const handleAddEvent = () => {
    // Function to add a new event
    console.log("Add event clicked");
  };

  const handleEventClick = (event: Event) => {
    // Function to handle event click
    console.log("Event clicked:", event);
  };

  const handleKeyDown = (e: React.KeyboardEvent, callback: () => void) => {
    if (e.key === "Enter" || e.key === " ") {
      callback();
    }
  };

  return (
    <div className="bg-[#18191b] border rounded-3xl p-5 w-[350px] text-white shadow-lg">
      <div className="flex justify-between items-center mb-4">
        <h2 className="text-2xl font-semibold">{currentMonth}</h2>
        <button 
          aria-label="Add event" 
          className="bg-[#303030] w-8 h-8 rounded-full flex items-center justify-center hover:bg-[#404040] transition-colors"
          onClick={handleAddEvent}
          onKeyDown={(e) => handleKeyDown(e, handleAddEvent)}
          tabIndex={0}
        >
          <span className="text-xl relative top-[-3px]">+</span>
        </button>
      </div>

      <div className="space-y-4">
        {days.map((day) => (
          <div key={day.dayOfMonth} className="flex">
            <div className="flex flex-col items-center mr-4 w-10">
              <span className="text-xs text-gray-400">{day.dayOfWeek}</span>
              <span className="text-lg font-medium">{day.dayOfMonth}</span>
            </div>
            
            <div className="flex-1">
              {day.events.length === 0 ? (
                <div className="bg-[#252525] rounded-lg p-3 text-gray-400 text-sm">
                  Nothing Scheduled for Today
                </div>
              ) : (
                <div className="space-y-2">
                  {day.events.map((event) => (
                    <div 
                      key={event.id}
                      className={`rounded-lg p-3 cursor-pointer ${
                        event.isPurple ? 'bg-[#1d4ed8]' : 'bg-[#252525]'
                      }`}
                      onClick={() => handleEventClick(event)}
                      onKeyDown={(e) => handleKeyDown(e, () => handleEventClick(event))}
                      tabIndex={0}
                      aria-label={`${event.title} from ${event.startTime} to ${event.endTime}`}
                    >
                      <div className="text-sm font-medium">{event.title}</div>
                      <div className="text-xs opacity-80">
                        {event.startTime} - {event.endTime}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default CalendarWidget;
