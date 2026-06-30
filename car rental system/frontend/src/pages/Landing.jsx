import React from 'react';
import { Link } from 'react-router-dom';
import { ArrowRight, ShieldCheck, Zap, Clock } from 'lucide-react';

const Landing = () => {
  return (
    <div className="pt-24 pb-16">
      {/* Hero Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-12 pb-20 md:pt-20 md:pb-32">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          
          {/* Left Column - Copy */}
          <div className="flex flex-col gap-6 text-center lg:text-left relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 w-fit mx-auto lg:mx-0">
              <Zap className="w-4 h-4" />
              <span className="text-sm font-medium">The Future of Car Rentals</span>
            </div>
            
            <h1 className="text-5xl md:text-7xl font-extrabold tracking-tight leading-[1.1]">
              Drive Without <br/>
              <span className="text-transparent bg-clip-text bg-gradient-to-r from-blue-500 to-cyan-300">
                Limits.
              </span>
            </h1>
            
            <p className="text-lg md:text-xl text-gray-400 max-w-xl mx-auto lg:mx-0 leading-relaxed">
              Experience seamless, AI-powered car rentals. Book in 60 seconds, unlock with your phone, and hit the road instantly. No queues, no paperwork.
            </p>
            
            <div className="flex flex-col sm:flex-row gap-4 mt-4 justify-center lg:justify-start">
              <Link to="/cars" className="btn-primary text-lg px-8 py-4 flex items-center justify-center gap-2 group">
                Browse Fleet 
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </Link>
              <Link to="/about" className="btn-outline text-lg px-8 py-4">
                How it Works
              </Link>
            </div>
            
            {/* Quick Stats */}
            <div className="grid grid-cols-3 gap-4 mt-8 pt-8 border-t border-white/10">
              <div>
                <p className="text-3xl font-bold text-white">500+</p>
                <p className="text-sm text-gray-400 mt-1">Premium Cars</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-white">50k+</p>
                <p className="text-sm text-gray-400 mt-1">Happy Drivers</p>
              </div>
              <div>
                <p className="text-3xl font-bold text-white">4.9/5</p>
                <p className="text-sm text-gray-400 mt-1">App Rating</p>
              </div>
            </div>
          </div>

          {/* Right Column - Visual/Interactive */}
          <div className="relative z-10 w-full h-[400px] md:h-[500px] lg:h-[600px] flex items-center justify-center">
            {/* We'll use a placeholder image for now, later we'll use Unsplash or AI generated image */}
            <div className="absolute inset-0 bg-gradient-to-tr from-blue-600/20 to-emerald-500/20 rounded-3xl blur-3xl" />
            <div className="glass-card w-full h-full p-8 flex flex-col justify-between relative overflow-hidden transform transition-transform hover:scale-[1.02] duration-500">
              <div className="flex justify-between items-start">
                <div>
                  <h3 className="text-2xl font-bold text-white">Tesla Model S Plaid</h3>
                  <p className="text-blue-400 font-medium">Electric • Luxury</p>
                </div>
                <div className="badge-available text-sm px-3 py-1">Available Now</div>
              </div>
              
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[120%] h-auto drop-shadow-2xl opacity-90">
                 {/* In a real app, you'd have an image of a car here. Since we're in beast mode, I'll generate one later */}
                 <div className="w-[80%] h-48 mx-auto bg-gradient-to-r from-gray-800 to-gray-700 rounded-2xl flex items-center justify-center border border-white/10 shadow-2xl">
                    <Car className="w-24 h-24 text-gray-500 opacity-50" />
                 </div>
              </div>

              <div className="bg-black/40 backdrop-blur-md rounded-xl p-4 flex justify-between items-center border border-white/10 z-10">
                <div>
                  <p className="text-sm text-gray-400">Starting from</p>
                  <p className="text-2xl font-bold text-white">$120<span className="text-sm font-normal text-gray-400">/day</span></p>
                </div>
                <Link to="/book/1" className="btn-primary">Reserve</Link>
              </div>
            </div>
          </div>

        </div>
      </section>

      {/* Features Section */}
      <section className="bg-white/5 border-y border-white/5 py-24">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-3xl md:text-4xl font-bold mb-4">Why Choose DRIVEFLOW?</h2>
            <p className="text-gray-400 max-w-2xl mx-auto">We've completely re-engineered the car rental experience to be faster, safer, and entirely digital.</p>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="glass-card p-8 hover:-translate-y-2 transition-transform duration-300">
              <div className="w-14 h-14 rounded-2xl bg-blue-500/10 flex items-center justify-center mb-6">
                <Zap className="w-7 h-7 text-blue-400" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">Instant Booking</h3>
              <p className="text-gray-400">No queues, no counters. Browse, book, and unlock your vehicle entirely through our web platform.</p>
            </div>
            
            <div className="glass-card p-8 hover:-translate-y-2 transition-transform duration-300">
              <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 flex items-center justify-center mb-6">
                <ShieldCheck className="w-7 h-7 text-emerald-400" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">Verified Safe</h3>
              <p className="text-gray-400">All vehicles undergo strict 50-point maintenance checks. Your safety is our highest priority.</p>
            </div>
            
            <div className="glass-card p-8 hover:-translate-y-2 transition-transform duration-300">
              <div className="w-14 h-14 rounded-2xl bg-amber-500/10 flex items-center justify-center mb-6">
                <Clock className="w-7 h-7 text-amber-400" />
              </div>
              <h3 className="text-xl font-bold text-white mb-3">24/7 Support & AI</h3>
              <p className="text-gray-400">Got an issue? Our AI assistant and 24/7 human support team are always just one tap away.</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};

export default Landing;
