import React, { useState, useEffect } from 'react';
import { Search, Filter, Star, Fuel, CheckCircle2, ChevronRight } from 'lucide-react';

import { getVehicles } from '../lib/api';

const Cars = () => {
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');
  const [cars, setCars] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const fetchCars = async () => {
      try {
        const data = await getVehicles();
        setCars(data);
      } catch (error) {
        console.error("Failed to fetch vehicles:", error);
      } finally {
        setLoading(false);
      }
    };
    fetchCars();
  }, []);
  
  const categories = ['All', 'Sedan', 'SUV', 'Luxury', 'Electric'];
  
  // Filter logic
  const filteredCars = cars.filter(car => {
    const matchesSearch = car.model.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = categoryFilter === 'All' || car.category.includes(categoryFilter) || car.fuel.includes(categoryFilter);
    return matchesSearch && matchesCategory;
  });

  return (
    <div className="pt-28 pb-20 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-end gap-6 mb-12">
        <div>
          <h1 className="text-4xl font-bold mb-3">Our Premium Fleet</h1>
          <p className="text-gray-400">Choose from our curated collection of top-tier vehicles.</p>
        </div>
        
        {/* Search & Filter Bar */}
        <div className="w-full md:w-auto flex flex-col sm:flex-row gap-3">
          <div className="relative group w-full sm:w-64">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-500 group-focus-within:text-blue-500 transition-colors" />
            <input 
              type="text" 
              placeholder="Search models..." 
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field pl-10 bg-white/5 border-white/10"
            />
          </div>
          <div className="flex gap-2 overflow-x-auto pb-2 sm:pb-0 scrollbar-hide w-full sm:w-auto">
            {categories.map(cat => (
              <button 
                key={cat}
                onClick={() => setCategoryFilter(cat)}
                className={`whitespace-nowrap px-4 py-2 rounded-lg font-medium transition-colors border ${
                  categoryFilter === cat 
                    ? 'bg-blue-600/20 text-blue-400 border-blue-500/30' 
                    : 'bg-white/5 text-gray-400 border-white/10 hover:bg-white/10'
                }`}
              >
                {cat}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Cars Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
        {filteredCars.map(car => (
          <div key={car.id} className="glass-card overflow-hidden flex flex-col group hover:-translate-y-1 transition-transform duration-300">
            {/* Image Placeholder */}
            <div className="h-56 bg-gradient-to-tr from-gray-800 to-gray-700 relative p-4 flex items-end">
              <div className="absolute inset-0 flex items-center justify-center opacity-30 group-hover:opacity-50 transition-opacity">
                <CarPlaceholder className="w-32 h-32 text-gray-500" />
              </div>
              <div className="relative z-10 flex justify-between w-full">
                <span className={`px-2.5 py-1 rounded-md text-xs font-bold uppercase tracking-wider backdrop-blur-md ${
                  car.status === 'AVAILABLE' ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 
                  car.status === 'RENTED' ? 'bg-amber-500/20 text-amber-400 border border-amber-500/30' : 
                  'bg-red-500/20 text-red-400 border border-red-500/30'
                }`}>
                  {car.status}
                </span>
                <span className="bg-black/60 backdrop-blur-md px-2.5 py-1 rounded-md text-xs font-medium text-white border border-white/10 flex items-center gap-1">
                  <Star className="w-3 h-3 text-yellow-500 fill-yellow-500" /> {car.rating}
                </span>
              </div>
            </div>
            
            {/* Content */}
            <div className="p-6 flex-grow flex flex-col">
              <div className="flex justify-between items-start mb-2">
                <h3 className="text-xl font-bold text-white truncate pr-4">{car.model}</h3>
              </div>
              
              <div className="flex items-center gap-4 text-sm text-gray-400 mb-6">
                <span className="flex items-center gap-1.5"><Fuel className="w-4 h-4" /> {car.fuel}</span>
                <span className="w-1 h-1 rounded-full bg-gray-600"></span>
                <span>{car.category}</span>
              </div>
              
              <div className="mt-auto pt-4 border-t border-white/10 flex justify-between items-center">
                <div>
                  <span className="text-2xl font-bold text-white">${car.price}</span>
                  <span className="text-gray-400 text-sm">/day</span>
                </div>
                <button 
                  disabled={car.status !== 'AVAILABLE'}
                  className={`btn-primary flex items-center gap-1.5 ${car.status !== 'AVAILABLE' ? 'opacity-50 cursor-not-allowed bg-gray-700 hover:bg-gray-700' : ''}`}
                >
                  {car.status === 'AVAILABLE' ? 'Book' : 'Waitlist'} <ChevronRight className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        ))}
      </div>
      
      {filteredCars.length === 0 && (
        <div className="text-center py-20 glass-card">
          <Search className="w-12 h-12 text-gray-500 mx-auto mb-4" />
          <h3 className="text-xl font-bold text-white mb-2">No cars found</h3>
          <p className="text-gray-400">Try adjusting your search or filters.</p>
        </div>
      )}
    </div>
  );
};

// Simple placeholder icon for cars
const CarPlaceholder = ({ className }) => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1" strokeLinecap="round" strokeLinejoin="round" className={className}>
    <path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2" />
    <circle cx="7" cy="17" r="2" />
    <path d="M9 17h6" />
    <circle cx="17" cy="17" r="2" />
  </svg>
);

export default Cars;
