import React from 'react';
import './SearchFilter.css';

const SearchFilter = ({ filters, setFilters }) => {
  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  return (
    <div className="search-filter">
      <div className="filter-group">
        <label>Category:</label>
        <select 
          value={filters.category} 
          onChange={(e) => handleFilterChange('category', e.target.value)}
        >
          <option value="">All Categories</option>
          <option value="CONCERT">Concert</option>
          <option value="SPORTS">Sports</option>
          <option value="THEATER">Theater</option>
          <option value="CONFERENCE">Conference</option>
        </select>
      </div>

      <div className="filter-group">
        <label>Location:</label>
        <input 
          type="text"
          placeholder="Enter city"
          value={filters.location}
          onChange={(e) => handleFilterChange('location', e.target.value)}
        />
      </div>

      <div className="filter-group">
        <label>Date:</label>
        <input 
          type="date"
          value={filters.date}
          onChange={(e) => handleFilterChange('date', e.target.value)}
        />
      </div>

      <div className="filter-group">
        <label>Price Range:</label>
        <select 
          value={filters.priceRange} 
          onChange={(e) => handleFilterChange('priceRange', e.target.value)}
        >
          <option value="">Any Price</option>
          <option value="0-1000">Under LKR 1,000</option>
          <option value="1000-5000">LKR 1,000 - 5,000</option>
          <option value="5000-10000">LKR 5,000 - 10,000</option>
          <option value="10000+">Above LKR 10,000</option>
        </select>
      </div>
    </div>
  );
};

export default SearchFilter;