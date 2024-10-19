import React, { useEffect, useRef } from 'react';
import { Heart, Globe, Shield, BarChart, File, Rss, ChevronDown, Search, Inbox, FileText, Send, Trash2, Archive, Users, Bell, ShoppingCart, Zap } from 'lucide-react';
import EmailToolAd from './EmailToolAd.js';

const EmailInterface = () => {
  return (
    <div className="w-full max-w-5xl bg-zinc-900 rounded-lg overflow-hidden shadow-2xl">
      <div className="bg-zinc-800 p-2 flex items-center space-x-2">
        <div className="w-3 h-3 rounded-full bg-red-500"></div>
        <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
        <div className="w-3 h-3 rounded-full bg-green-500"></div>
      </div>
      <div className="flex">
        {/* Sidebar */}
        <div className="w-1/4 bg-zinc-900 p-4 border-r border-zinc-800">
          <div className="flex items-center mb-6">
            <div className="w-8 h-8 bg-zinc-700 rounded-full mr-2"></div>
            <div className="text-sm font-semibold">Alicia Koch</div>
            <ChevronDown size={16} className="ml-auto" />
          </div>
          <div className="space-y-2">
            {[
              { icon: Inbox, label: 'Inbox', count: 128 },
              { icon: FileText, label: 'Drafts', count: 9 },
              { icon: Send, label: 'Sent', count: null },
              { icon: Trash2, label: 'Junk', count: 23 },
              { icon: Trash2, label: 'Trash', count: null },
              { icon: Archive, label: 'Archive', count: null },
              { icon: Users, label: 'Social', count: 972 },
              { icon: Bell, label: 'Updates', count: 342 },
              { icon: Users, label: 'Forums', count: 128 },
              { icon: ShoppingCart, label: 'Shopping', count: 8 },
              { icon: Zap, label: 'Promotions', count: 21 }
            ].map(({ icon: Icon, label, count }, index) => (
              <div key={index} className="flex items-center text-zinc-400 hover:text-white">
                <Icon size={16} className="mr-2" />
                <span>{label}</span>
                {count !== null && <span className="ml-auto">{count}</span>}
              </div>
            ))}
          </div>
        </div>

        {/* Main Content */}
        <div className="w-3/4 p-4">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-xl font-bold">Inbox</h2>
            <div className="flex space-x-2">
              <button className="bg-zinc-800 px-3 py-1 rounded text-sm">All mail</button>
              <button className="bg-zinc-800 px-3 py-1 rounded text-sm">Unread</button>
            </div>
          </div>
          <div className="bg-zinc-800 p-2 rounded mb-4 flex items-center">
            <Search size={16} className="text-zinc-400 mr-2" />
            <input type="text" placeholder="Search" className="bg-transparent text-sm w-full outline-none" />
          </div>
          {/* Email List */}
          <div className="space-y-2">
            {[
              { name: 'William Smith', subject: 'Meeting Tomorrow', time: '4 months ago', preview: 'Hi, let\'s have a meeting tomorrow to discuss the project. I\'ve been reviewing the project...' },
              { name: 'Alice Smith', subject: 'Re: Project Update', time: '4 months ago', preview: 'Thank you for the project update. It looks great! I\'ve gone through the report, and the...' },
              { name: 'Bob Johnson', subject: 'Weekend Plans', time: '5 months ago', preview: 'Hey team, I hope this email finds you well. I wanted to touch base about our plans for the...' }
            ].map((email, index) => (
              <div key={index} className="bg-zinc-800 p-3 rounded">
                <div className="flex justify-between items-center mb-1">
                  <span className="font-semibold">{email.name}</span>
                  <span className="text-xs text-zinc-400">{email.time}</span>
                </div>
                <div className="text-sm font-medium mb-1">{email.subject}</div>
                <div className="text-xs text-zinc-400">{email.preview}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

const LandingPage = () => {
    const iconRef = useRef(null);
  
    useEffect(() => {
      const icons = iconRef.current.children;
      let index = 0;
      const interval = setInterval(() => {
        icons[index].style.opacity = '0';
        index = (index + 1) % icons.length;
        icons[index].style.opacity = '1';
      }, 2000);
      return () => clearInterval(interval);
    }, []);
  
    return (
      <div className="min-h-screen flex flex-col bg-black text-white overflow-hidden">
        <header className="p-6 flex justify-between items-center z-10">
          <div className="text-sm font-bold">i love email lol</div>
          <div className="space-x-6">
            <button className="text-sm">Log in</button>
            <button className="text-sm bg-zinc-800 text-white px-4 py-2 rounded-full">Sign up</button>
          </div>
        </header>
  
        <main className="flex-grow flex flex-col items-center justify-center text-center px-4 relative mt-16">
          <div ref={iconRef} className="absolute inset-0 flex items-center justify-center opacity-5">
            {[Heart, Globe, Shield, BarChart, File, Rss].map((Icon, index) => (
              <Icon key={index} size={400} className="absolute transition-opacity duration-1000" style={{opacity: index === 0 ? 1 : 0}} />
            ))}
          </div>
  
          <h1 className="text-6xl sm:text-7xl font-bold mb-6 relative z-10 bg-clip-text bg-gradient-to-b from-white to-gray-400">
  a new way to<br />
  <span className="relative inline-block">
    love email again.
    <svg className="absolute -bottom-2 left-0 w-full" height="10" viewBox="0 0 300 10" preserveAspectRatio="none">
      <path d="M0,5 C50,0 100,10 150,5 C200,0 250,10 300,5" fill="none" stroke="#4ade80" strokeWidth="2" />
    </svg>
  </span>
</h1>
          <p className="text-zinc-400 text-lg mb-8 max-w-2xl relative z-10">
            proactively manage your life with the elegance of<br />
            a truly personal inbox powered by artificial intelligence.
          </p>
          <button className="bg-white text-black px-6 py-3 rounded-full text-sm font-bold relative z-10 hover:bg-gray-200 transition-colors">
            Get Started →
          </button>
  
          <div className="mt-16 relative z-10">
            <EmailInterface />
          </div>
  
          <div className="mt-16 w-full">
            <EmailToolAd />
          </div>
  
          <div className="h-64"></div>
        </main>

      <footer className="bg-black text-white py-16">
        <div className="max-w-5xl mx-auto px-4">
          <div className="mb-16">
            <div className="flex items-center mb-4">
              <div className="w-12 h-12 bg-gradient-to-br from-pink-500 to-orange-400 rounded-2xl mr-3"></div>
              <h2 className="text-3xl font-bold">i love email lol</h2>
            </div>
            <p className="text-zinc-400">an AI powered inbox for an AI powered life.</p>
          </div>
          
          <div className="grid grid-cols-3 gap-x-24 gap-y-8 text-sm">
            <div>
              <h3 className="font-bold mb-4">PRODUCT</h3>
              <ul className="space-y-2">
                <li><a href="#" className="text-zinc-400 hover:text-white">Email Collection</a></li>
                <li><a href="#" className="text-zinc-400 hover:text-white">Pricing</a></li>
                <li><a href="#" className="text-zinc-400 hover:text-white">FAQ</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold mb-4">COMMUNITY</h3>
              <ul className="space-y-2">
                <li><a href="#" className="text-zinc-400 hover:text-white">Discord</a></li>
                <li><a href="#" className="text-zinc-400 hover:text-white">Twitter</a></li>
                <li><a href="#" className="text-zinc-400 hover:text-white">Email</a></li>
              </ul>
            </div>
            <div>
              <h3 className="font-bold mb-4">LEGAL</h3>
              <ul className="space-y-2">
                <li><a href="#" className="text-zinc-400 hover:text-white">Terms</a></li>
                <li><a href="#" className="text-zinc-400 hover:text-white">Privacy</a></li>
              </ul>
            </div>
          </div>

          <div className="flex justify-between items-center pt-16 border-t border-zinc-800 mt-16">
            <div className="flex space-x-4">
              <a href="#" className="text-zinc-400 hover:text-white">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M8.9 8.9v6.2h6.2V8.9H8.9z"/><path d="M15.5 7.5l-3.9-3.9c-.2-.2-.5-.2-.7 0l-3.9 3.9c-.1.1-.1.2-.1.3v9.3c0 .3.2.5.5.5h9.3c.3 0 .5-.2.5-.5v-9.3c0-.1 0-.2-.1-.3z"/></svg>
              </a>
              <a href="#" className="text-zinc-400 hover:text-white">
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 4s-.7 2.1-2 3.4c1.6 10-9.4 17.3-18 11.6 2.2.1 4.4-.6 6-2C3 15.5.5 9.6 3 5c2.2 2.6 5.6 4.1 9 4-.9-4.2 4-6.6 7-3.8 1.1 0 3-1.2 3-1.2z"/></svg>
              </a>
            </div>
            <p className="text-zinc-400 text-sm">Copyright © 2024 i love email lol. All Rights Reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default LandingPage;