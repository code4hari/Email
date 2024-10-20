import React, { useState } from 'react';

const LoginPage = () => {
  const [emailSummary, setEmailSummary] = useState('');
  const [categories, setCategories] = useState('');
  const [isSummarizing, setIsSummarizing] = useState(false);
  const [isCategorizing, setIsCategorizing] = useState(false);
  const [isScheduling, setIsScheduling] = useState(false);
  const [isRecommending, setIsRecommending] = useState(false);

  const handleApiError = (error, message) => {
    console.error(message, error);
    alert(`${message}. Please try again.`);
  };

  const handleSummarizeEmails = async () => {
    setIsSummarizing(true);
  
    const myHeaders = new Headers();
    myHeaders.append('Content-Type', 'application/json');
  
    const categoriesArray = categories.split(',').map((c) => c.trim()); 
    const raw = JSON.stringify({
      categories: categoriesArray,
    });
  
    const requestOptions = {
      method: 'POST',
      headers: myHeaders,
      body: raw,
      redirect: 'follow',
    };
  
    try {
      const response = await fetch('http://127.0.0.1:5000/api/categorize_emails', requestOptions);
      const result = await response.text();
      console.log(result);
      setEmailSummary(result); 
    } catch (error) {
      handleApiError(error, 'Error summarizing emails');
    } finally {
      setIsSummarizing(false);
    }
  };
  

  const handleCategorizeEmails = async () => {
    setIsCategorizing(true);

    const myHeaders = new Headers();
    myHeaders.append('Content-Type', 'application/json');

    const categoriesArray = categories.split(',').map((c) => c.trim());
    const raw = JSON.stringify({ categories: categoriesArray });

    const requestOptions = {
      method: 'POST',
      headers: myHeaders,
      body: raw,
      redirect: 'follow',
    };

    try {
      const response = await fetch('http://127.0.0.1:5000/api/categorize_emails', requestOptions);
      const result = await response.text();
      console.log(result);
      alert('Emails categorized successfully!');
    } catch (error) {
      handleApiError(error, 'Error categorizing emails');
    } finally {
      setIsCategorizing(false);
    }
  };

  const handleScheduleEmails = async () => {
    setIsScheduling(true);
    const requestOptions = {
      method: 'POST',
      redirect: 'follow',
    };

    try {
      const response = await fetch('http://172.210.16.114:6060/api/linear_updates', requestOptions);
      const result = await response.text();
      console.log(result);
      alert('Emails scheduled successfully!');
    } catch (error) {
      handleApiError(error, 'Error scheduling emails');
    } finally {
      setIsScheduling(false);
    }
  };

  const handleFollowUpRecommendations = async () => {
    setIsRecommending(true);
    const requestOptions = {
      method: 'POST',
      redirect: 'follow',
    };

    try {
      const response = await fetch('http://172.210.16.114:6060/api/process_emails', requestOptions);
      const result = await response.text();
      console.log(result);
      alert('Follow-up recommendations generated successfully!');
    } catch (error) {
      handleApiError(error, 'Error getting follow-up recommendations');
    } finally {
      setIsRecommending(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-100 py-6 flex flex-col justify-center sm:py-12">
      <div className="relative py-3 sm:max-w-xl sm:mx-auto">
        <div className="relative px-4 py-10 bg-white shadow-lg sm:rounded-3xl sm:p-20">
          <div className="max-w-md mx-auto">
            <h2 className="text-2xl font-bold mb-4">Email Management Dashboard</h2>

            {/* Email Summarization */}
            <div className="mb-6">
              <button
                onClick={handleSummarizeEmails}
                disabled={isSummarizing}
                className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded"
              >
                {isSummarizing ? 'Summarizing...' : 'Summarize Emails'}
              </button>
              {emailSummary && (
                <div className="mt-4 p-4 border rounded">
                  <h3 className="font-bold mb-2">Email Summary</h3>
                  <p>{emailSummary}</p>
                </div>
              )}
            </div>

            {/* Email Categorization */}
            <div className="mb-6">
              <input
                type="text"
                placeholder="Enter categories (comma-separated)"
                value={categories}
                onChange={(e) => setCategories(e.target.value)}
                className="mb-2 p-2 border rounded w-full"
              />
              <button
                onClick={handleCategorizeEmails}
                disabled={isCategorizing || !categories}
                className="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded"
              >
                {isCategorizing ? 'Categorizing...' : 'Categorize Emails'}
              </button>
            </div>

            {/* Automatic Scheduler */}
            <div className="mb-6">
              <button
                onClick={handleScheduleEmails}
                disabled={isScheduling}
                className="bg-yellow-500 hover:bg-yellow-700 text-white font-bold py-2 px-4 rounded"
              >
                {isScheduling ? 'Scheduling...' : 'Schedule Emails'}
              </button>
            </div>

            {/* Follow-up Recommender */}
            <div className="mb-6">
              <button
                onClick={handleFollowUpRecommendations}
                disabled={isRecommending}
                className="bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded"
              >
                {isRecommending ? 'Getting Recommendations...' : 'Get Follow-up Recommendations'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
