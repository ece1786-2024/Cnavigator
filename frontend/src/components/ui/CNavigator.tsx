import React, { useState } from 'react';
import { MessageCircle, Book, CheckCircle, AlertCircle } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from './card';
import { Alert, AlertDescription } from './alert';

const CNavigator = () => {
  const [currentView, setCurrentView] = useState('welcome');
  const [teachingStyle, setTeachingStyle] = useState('');
  const [userInput, setUserInput] = useState('');
  const [messages, setMessages] = useState([]);
  const [currentChapter, setCurrentChapter] = useState(null);
  const [isQuizMode, setIsQuizMode] = useState(false);

  // Simulated chapter data
  const chapters = [
    { id: 1, name: 'Introduction to C', completed: false },
    { id: 2, name: 'Variables and Data Types', completed: false },
    { id: 3, name: 'Control Structures', completed: false },
    { id: 4, name: 'Functions', completed: false },
  ];

  const handleTeachingStyleSubmit = () => {
    if (teachingStyle) {
      setMessages([
        {
          type: 'system',
          content: `Welcome! I'll be your ${teachingStyle} guide through C programming.`
        }
      ]);
      setCurrentView('initialTest');
    }
  };

  const handleMessageSubmit = () => {
    if (!userInput.trim()) return;

    setMessages(prev => [...prev, {
      type: 'user',
      content: userInput
    }]);

    // Simulate response based on input
    if (userInput.toLowerCase() === 'cccc') {
      if (isQuizMode) {
        setIsQuizMode(false);
        setMessages(prev => [...prev, {
          type: 'system',
          content: 'Moving to the next section...'
        }]);
      } else {
        setIsQuizMode(true);
        setMessages(prev => [...prev, {
          type: 'system',
          content: "Great! Let's test your knowledge with a quick quiz."
        }]);
      }
    } else {
      setMessages(prev => [...prev, {
        type: 'system',
        content: isQuizMode ? 
          'Your answer has been recorded. Would you like to try again? (Type "cccc" to move on)' :
          'Great question! Would you like to know more? (Type "cccc" for quiz)'
      }]);
    }
    
    setUserInput('');
  };

  const renderView = () => {
    switch (currentView) {
      case 'welcome':
        return (
          <Card className="w-full max-w-2xl mx-auto">
            <CardHeader>
              <CardTitle className="text-2xl">Welcome to CNavigator</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <p className="text-gray-600">
                  Welcome to the CNavigator learning platform! We're here to help you master C programming, 
                  from basics to advanced levels. Let's begin this exciting journey together!
                </p>
                <div className="space-y-2">
                  <label className="block text-sm font-medium">
                    What teaching style do you prefer?
                  </label>
                  <input
                    type="text"
                    value={teachingStyle}
                    onChange={(e) => setTeachingStyle(e.target.value)}
                    placeholder="Enter an adjective (e.g., 'humorous')"
                    className="w-full p-2 border rounded-md"
                  />
                  <button
                    onClick={handleTeachingStyleSubmit}
                    className="w-full bg-blue-600 text-white py-2 rounded-md hover:bg-blue-700"
                  >
                    Start Learning
                  </button>
                </div>
              </div>
            </CardContent>
          </Card>
        );

      case 'initialTest':
      case 'learning':
        return (
          <div className="w-full max-w-4xl mx-auto space-y-4">
            {/* Chapter Progress */}
            <Card>
              <CardContent className="pt-6">
                <div className="grid grid-cols-4 gap-4">
                  {chapters.map(chapter => (
                    <div
                      key={chapter.id}
                      className={`p-4 rounded-lg border ${
                        currentChapter?.id === chapter.id
                          ? 'border-blue-500 bg-blue-50'
                          : chapter.completed
                          ? 'border-green-500 bg-green-50'
                          : 'border-gray-200'
                      }`}
                    >
                      <div className="flex items-center space-x-2">
                        {chapter.completed ? (
                          <CheckCircle className="w-5 h-5 text-green-500" />
                        ) : (
                          <Book className="w-5 h-5 text-gray-500" />
                        )}
                        <span className="text-sm">{chapter.name}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Chat Interface */}
            <Card className="h-[600px] flex flex-col">
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <MessageCircle className="w-5 h-5" />
                  <span>{isQuizMode ? 'Quiz Mode' : 'Learning Mode'}</span>
                </CardTitle>
              </CardHeader>
              <CardContent className="flex-1 flex flex-col">
                <div className="flex-1 overflow-y-auto space-y-4 mb-4">
                  {messages.map((msg, idx) => (
                    <div
                      key={idx}
                      className={`flex ${
                        msg.type === 'user' ? 'justify-end' : 'justify-start'
                      }`}
                    >
                      <div
                        className={`max-w-[80%] p-3 rounded-lg ${
                          msg.type === 'user'
                            ? 'bg-blue-600 text-white'
                            : 'bg-gray-100'
                        }`}
                      >
                        {msg.content}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="flex space-x-2">
                  <input
                    type="text"
                    value={userInput}
                    onChange={(e) => setUserInput(e.target.value)}
                    placeholder={isQuizMode ? "Type your answer..." : "Ask a question..."}
                    className="flex-1 p-2 border rounded-md"
                    onKeyPress={(e) => e.key === 'Enter' && handleMessageSubmit()}
                  />
                  <button
                    onClick={handleMessageSubmit}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                  >
                    Send
                  </button>
                </div>
              </CardContent>
            </Card>

            {/* Quick Tips */}
            <Alert>
              <AlertCircle className="w-4 h-4" />
              <AlertDescription>
                Type "cccc" to {isQuizMode ? 'move to the next section' : 'start the quiz'}
              </AlertDescription>
            </Alert>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-4">
      {renderView()}
    </div>
  );
};

export default CNavigator;