import React, { useState, useEffect, useRef } from 'react';

// API Configuration
const API_BASE = window.location.port === '5173' ? 'http://localhost:8000' : '';

// Types for Recommendations API response
interface Restaurant {
  restaurant_id: string;
  name: string;
  location: string;
  cuisine: string;
  estimated_cost: string;
  rating: number;
  rank: number;
  explanation: string;
  budget_tier: string;
  metadata?: {
    address?: string;
    area?: string;
    listed_area?: string;
    votes?: number;
    rest_type?: string;
    online_order?: string;
    book_table?: string;
    dish_liked?: string;
    url?: string;
  };
}

interface RecommendationsResponse {
  success: boolean;
  summary?: string;
  recommendations: Restaurant[];
  used_fallback: boolean;
  error?: string;
}

interface DatasetStats {
  cities: string[];
  location_options: string[];
  cuisines: string[];
  budget_tiers: string[];
}

// Cuisine image curation
const getCuisineImage = (cuisine: string): string => {
  const cuisineLower = cuisine.toLowerCase();
  const images: Record<string, string> = {
    italian: "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&h=300&fit=crop",
    chinese: "https://images.unsplash.com/photo-1563245372-f21724e3856d?w=400&h=300&fit=crop",
    "north indian": "https://images.unsplash.com/photo-1585938338392-50a5d22b6c7d?w=400&h=300&fit=crop",
    "south indian": "https://images.unsplash.com/photo-1589301760014-d929f3979dbc?w=400&h=300&fit=crop",
    continental: "https://images.unsplash.com/photo-1546069901-ba9599a7e63c?w=400&h=300&fit=crop",
    mexican: "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=400&h=300&fit=crop",
    desserts: "https://images.unsplash.com/photo-1551024601-bec78aea704b?w=400&h=300&fit=crop",
    cafe: "https://images.unsplash.com/photo-1554118811-1e0d58224f24?w=400&h=300&fit=crop",
    beverages: "https://images.unsplash.com/photo-1497534446932-c925b458314e?w=400&h=300&fit=crop",
  };

  for (const [key, url] of Object.entries(images)) {
    if (cuisineLower.includes(key)) {
      return url;
    }
  }
  return "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&h=300&fit=crop";
};

// Cuisine emoji helper
const getCuisineIcon = (cuisine: string): string => {
  const c = cuisine.toLowerCase();
  if (c.includes('italian') || c.includes('pizza') || c.includes('pasta')) return '🍕';
  if (c.includes('chinese') || c.includes('ramen') || c.includes('noodles') || c.includes('asian')) return '🥢';
  if (c.includes('north indian') || c.includes('punjabi') || c.includes('curry')) return '🍲';
  if (c.includes('south indian') || c.includes('dosa') || c.includes('idli')) return '🥞';
  if (c.includes('continental') || c.includes('french') || c.includes('european') || c.includes('bakery')) return '🥐';
  if (c.includes('mexican') || c.includes('taco') || c.includes('nacho')) return '🌮';
  if (c.includes('dessert') || c.includes('cake') || c.includes('ice cream')) return '🍨';
  if (c.includes('cafe') || c.includes('coffee') || c.includes('tea')) return '☕';
  if (c.includes('beverage') || c.includes('juice') || c.includes('drink')) return '🍹';
  return '🍱';
};

export default function App() {
  // App States
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);
  const [stats, setStats] = useState<DatasetStats>({
    cities: ["Bangalore"],
    location_options: ["Bangalore"],
    cuisines: ["Italian", "Chinese", "North Indian", "Continental"],
    budget_tiers: ["low", "medium", "high"],
  });

  // UI Flow States
  const [wizardActive, setWizardActive] = useState<boolean>(false);
  const [step, setStep] = useState<number>(1);
  const [autocompleteOpen, setAutocompleteOpen] = useState<boolean>(false);
  const [selectedPreset, setSelectedPreset] = useState<string | null>(null);
  
  // Modal Drawer Details
  const [drawerOpen, setDrawerOpen] = useState<boolean>(false);
  const [selectedRestaurant, setSelectedRestaurant] = useState<Restaurant | null>(null);

  // Filter States
  const [locationQuery, setLocationQuery] = useState<string>("Bangalore");
  const [location, setLocation] = useState<string>("Bangalore");
  const [selectedCuisine, setSelectedCuisine] = useState<string>("Any");
  const [budget, setBudget] = useState<string>("medium");
  const [minRating, setMinRating] = useState<number>(4.0);
  const [additionalPrefs, setAdditionalPrefs] = useState<string>("");
  const [topK, setTopK] = useState<number>(5);

  // Results & Interaction States
  const [loading, setLoading] = useState<boolean>(false);
  const [recommendations, setRecommendations] = useState<RecommendationsResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [darkMode, setDarkMode] = useState<boolean>(false);

  // Autocomplete ref
  const autocompleteRef = useRef<HTMLDivElement>(null);

  // Redesign Search States
  const [searchBarFocused, setSearchBarFocused] = useState<boolean>(false);
  const [localSearchQuery, setLocalSearchQuery] = useState<string>("");

  // Check API Health and Fetch Hints
  useEffect(() => {
    const initApp = async () => {
      try {
        const healthRes = await fetch(`${API_BASE}/health`);
        const healthData = await healthRes.json();
        const isOnline = healthRes.status === 200 && healthData.dataset_loaded;
        setApiOnline(isOnline);

        if (isOnline) {
          const statsRes = await fetch(`${API_BASE}/dataset/stats`);
          if (statsRes.status === 200) {
            const statsData = await statsRes.json();
            setStats(statsData);
            if (statsData.location_options && statsData.location_options.includes("Bangalore")) {
              setLocation("Bangalore");
              setLocationQuery("Bangalore");
            } else if (statsData.location_options && statsData.location_options.length > 0) {
              setLocation(statsData.location_options[0]);
              setLocationQuery(statsData.location_options[0]);
            }
          }
        }
      } catch (err) {
        console.error("Connection failed: Running in offline fallback.", err);
        setApiOnline(false);
      }
    };
    initApp();
  }, []);

  // Sync Dark Mode state to document root
  useEffect(() => {
    if (darkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [darkMode]);

  // Click outside autocomplete box handler
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (autocompleteRef.current && !autocompleteRef.current.contains(event.target as Node)) {
        setAutocompleteOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, []);

  // Handle Find Recommendations Trigger
  const handleSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setLoading(true);
    setError(null);
    setRecommendations(null);

    const cuisineValue = selectedCuisine === "Any" ? "Any" : selectedCuisine;
    const additionalList = additionalPrefs
      .split(",")
      .map(t => t.trim())
      .filter(t => t.length > 0);

    const payload = {
      location,
      budget,
      cuisine: cuisineValue,
      min_rating: minRating,
      additional_preferences: additionalList,
      top_k: topK,
    };

    try {
      const res = await fetch(`${API_BASE}/recommendations`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(`Server returned error ${res.status}: ${errText}`);
      }

      const data = await res.json();
      if (!data.success) {
        throw new Error(data.error || "Failed to retrieve recommendations.");
      }

      setRecommendations(data);
    } catch (err: any) {
      setError(err.message || "An unexpected error occurred.");
    } finally {
      setLoading(false);
    }
  };

  // Reset filter values and clean screen
  const handleReset = () => {
    setLocation("Bangalore");
    setLocationQuery("Bangalore");
    setSelectedCuisine("Any");
    setBudget("medium");
    setMinRating(4.0);
    setAdditionalPrefs("");
    setTopK(5);
    setSelectedPreset(null);
    setRecommendations(null);
    setError(null);
    setStep(1);
    setWizardActive(false);
  };

  // Preset Mapping Trigger
  const handlePresetSelect = (preset: string) => {
    if (preset === 'datenight') {
      setBudget("high");
      setMinRating(4.2);
      setTopK(3);
      setAdditionalPrefs("rooftop, romantic, intimate, fine dining");
      setSelectedPreset("datenight");
    } else if (preset === 'quicklunch') {
      setBudget("low");
      setMinRating(3.5);
      setTopK(3);
      setAdditionalPrefs("quick service, fast, casual, budget friendly");
      setSelectedPreset("quicklunch");
    } else if (preset === 'familydinner') {
      setBudget("medium");
      setMinRating(4.0);
      setTopK(5);
      setAdditionalPrefs("family friendly, group seating, quiet");
      setSelectedPreset("familydinner");
    }
  };

  // Autocomplete search suggestions list
  const getAutocompleteSuggestions = () => {
    if (!locationQuery || locationQuery.length < 2) return [];
    return stats.location_options.filter(opt => 
      opt.toLowerCase().includes(locationQuery.toLowerCase())
    ).slice(0, 5);
  };

  // Calculate Statistics for Ratings Distribution Chart
  const getRatingStats = () => {
    if (!recommendations || !recommendations.recommendations) return null;
    const list = recommendations.recommendations;
    const ratings = list.map(r => r.rating);
    const avg = ratings.length > 0 ? (ratings.reduce((a, b) => a + b, 0) / ratings.length) : 0;
    
    const dist = { 5: 0, 4: 0, 3: 0, 2: 0, 1: 0 };
    ratings.forEach(r => {
      if (r >= 4.5) dist[5]++;
      else if (r >= 3.5) dist[4]++;
      else if (r >= 2.5) dist[3]++;
      else if (r >= 1.5) dist[2]++;
      else dist[1]++;
    });

    const maxCount = Math.max(...Object.values(dist), 1);
    return { avg, dist, maxCount, total: ratings.length };
  };

  // Redesign Helper Methods
  const getActiveFiltersCount = () => {
    let count = 0;
    if (location) count++;
    if (selectedCuisine && selectedCuisine !== "Any") count++;
    if (budget) count++;
    if (minRating && minRating > 0) count++;
    if (additionalPrefs && additionalPrefs.trim().length > 0) count++;
    return count;
  };

  const handleSearchWithUpdatedParams = (removedType?: string) => {
    setLoading(true);
    setError(null);
    setRecommendations(null);

    const loc = removedType === 'location' 
      ? (stats.location_options.includes("Bangalore") ? "Bangalore" : stats.location_options[0]) 
      : location;
    const cuis = removedType === 'cuisine' ? "Any" : selectedCuisine;
    const budg = removedType === 'budget' ? "medium" : budget;
    const rat = removedType === 'rating' ? 0.0 : minRating;
    const vibes = removedType === 'vibes' ? "" : additionalPrefs;

    const additionalList = vibes
      .split(",")
      .map(t => t.trim())
      .filter(t => t.length > 0);

    const payload = {
      location: loc,
      budget: budg,
      cuisine: cuis === "Any" ? "Any" : cuis,
      min_rating: rat,
      additional_preferences: additionalList,
      top_k: topK,
    };

    fetch(`${API_BASE}/recommendations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(payload),
    })
    .then(res => {
      if (!res.ok) throw new Error(`Server returned error ${res.status}`);
      return res.json();
    })
    .then(data => {
      if (!data.success) throw new Error(data.error || "Failed to retrieve recommendations.");
      setRecommendations(data);
    })
    .catch(err => {
      setError(err.message || "An unexpected error occurred.");
    })
    .finally(() => {
      setLoading(false);
    });
  };

  const removeFilterPill = (type: string) => {
    if (type === 'location') {
      if (stats.location_options.length > 0) {
        const defaultLoc = stats.location_options.includes("Bangalore") ? "Bangalore" : stats.location_options[0];
        setLocation(defaultLoc);
        setLocationQuery(defaultLoc);
      }
    } else if (type === 'cuisine') {
      setSelectedCuisine("Any");
    } else if (type === 'budget') {
      setBudget("medium");
    } else if (type === 'rating') {
      setMinRating(0.0);
    } else if (type === 'vibes') {
      setAdditionalPrefs("");
    }
    setSelectedPreset(null);
    handleSearchWithUpdatedParams(type);
  };

  const chartStats = getRatingStats();
  const suggestions = getAutocompleteSuggestions();
  const filteredRecommendations = recommendations && recommendations.recommendations 
    ? recommendations.recommendations.filter(r => 
        r.name.toLowerCase().includes(localSearchQuery.toLowerCase()) ||
        r.cuisine.toLowerCase().includes(localSearchQuery.toLowerCase()) ||
        r.explanation.toLowerCase().includes(localSearchQuery.toLowerCase()) ||
        r.location.toLowerCase().includes(localSearchQuery.toLowerCase())
      )
    : [];

  return (
    <div className="app-container">
      {/* Top Application Bar */}
      <header className="top-bar">
        <div className="brand" onClick={handleReset} style={{ cursor: 'pointer' }}>
          <div className="brand-icon">🍕</div>
          <h1 className="brand-name font-display-lg">CraveAI</h1>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <button 
            onClick={() => setDarkMode(!darkMode)}
            className="theme-toggle-btn"
            aria-label="Toggle dark mode"
            style={{ border: 'none' }}
          >
            {darkMode ? "☀️" : "🌙"}
          </button>
          <div className="profile-avatar-bar">
            <img 
              src="https://lh3.googleusercontent.com/aida-public/AB6AXuD9szuzAPljpAhyZ7fmXeI3wlq60lKWzouctNmkHHiqtRZXZaw4jBx44IXhwoM7TH7ngTeYegHQDEu0HjcBWwqcMkfdCE67Nwiwpez63Wdr5ijiQvEpgMzoPeYh-SpkPCSLki1aeHqZhWsukVu0_q2w_JU7IAhGRJHm7ODXkIFbzikyjyhLpi7FruuPJmNLwYyDL9tqlPaziRHmLR7lAwRHGs05Ut-0exzgJFPb30WiXDZObMvAJ4joEjjZqZf_XTpKrMMO-h4YKGE"
              alt="Profile"
              className="profile-avatar-img"
            />
          </div>
        </div>
      </header>

      {/* API Connection Indicator */}
      {apiOnline !== null && (
        <div className={`status-badge ${apiOnline ? 'status-online' : 'status-offline'}`}>
          {apiOnline ? "🟢 Connected to Backend API" : "🟠 Running In-Process Fallback (Backend Offline)"}
        </div>
      )}

      {/* Main Grid Content Area */}
      <div className="dashboard-grid" style={{ gridTemplateColumns: recommendations || loading || error ? '1fr' : '1fr' }}>
        
        {loading ? (
          /* ==========================================
             LOADING SKELETON STATE
             ========================================== */
          <div style={{ width: '100%' }}>
            <h2 className="font-display-lg" style={{ fontSize: '32px', marginBottom: '24px', textAlign: 'center' }}>
              Finding your perfect match...
            </h2>
            <div className="cards-grid">
              {[1, 2, 3].map((i) => (
                <div key={i} className="restaurant-card" style={{ minHeight: '380px' }}>
                  <div className="image-container">
                    <div className="skeleton" style={{ width: '100%', height: '100%' }}></div>
                  </div>
                  <div className="card-details">
                    <div className="skeleton" style={{ width: '75%', height: '24px', marginBottom: '8px' }}></div>
                    <div className="skeleton" style={{ width: '40%', height: '16px', marginBottom: '16px' }}></div>
                    <div className="skeleton" style={{ width: '100%', height: '60px', marginTop: 'auto' }}></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : error ? (
          /* ==========================================
             ERROR FALLBACK STATE
             ========================================== */
          <div className="welcome-banner" style={{ background: 'rgba(186, 26, 26, 0.05)', borderColor: 'rgba(186, 26, 26, 0.1)' }}>
            <div className="welcome-emoji">⚠️</div>
            <h2 className="welcome-title" style={{ color: 'var(--primary)' }}>Recommendation Failed</h2>
            <p className="welcome-desc" style={{ color: 'var(--on-surface-variant)' }}>{error}</p>
            <button className="btn-primary" style={{ width: 'auto', margin: '0 auto' }} onClick={handleReset}>
              Try Resetting Search
            </button>
          </div>
        ) : recommendations ? (
          /* ==========================================
             RECOMMENDATIONS RESULTS LIST
             ========================================== */
          <div>
            {/* Search Input Bar */}
            <div className={`search-bar-container ${searchBarFocused ? 'focused' : ''}`}>
              <span className="material-symbols-outlined search-bar-icon">search</span>
              <input 
                type="text"
                className="search-bar-input"
                placeholder="Search cuisines, restaurants, or dishes..."
                value={localSearchQuery}
                onChange={(e) => setLocalSearchQuery(e.target.value)}
                onFocus={() => setSearchBarFocused(true)}
                onBlur={() => setSearchBarFocused(false)}
              />
            </div>

            {/* Active filter pills */}
            <div className="filter-pills-container">
              {location && (
                <div className="filter-pill" onClick={() => removeFilterPill('location')}>
                  <span className="filter-pill-label">Location:</span> {location}
                  <span className="filter-pill-close">✕</span>
                </div>
              )}
              {selectedCuisine && selectedCuisine !== 'Any' && (
                <div className="filter-pill" onClick={() => removeFilterPill('cuisine')}>
                  <span className="filter-pill-label">Cuisine:</span> {selectedCuisine}
                  <span className="filter-pill-close">✕</span>
                </div>
              )}
              {budget && (
                <div className="filter-pill" onClick={() => removeFilterPill('budget')}>
                  <span className="filter-pill-label">Budget:</span> {budget === 'low' ? 'Low' : budget === 'medium' ? 'Medium' : budget === 'high' ? 'High' : 'Fine Dining'}
                  <span className="filter-pill-close">✕</span>
                </div>
              )}
              {minRating > 0 && (
                <div className="filter-pill" onClick={() => removeFilterPill('rating')}>
                  <span className="filter-pill-label">Rating:</span> {minRating.toFixed(1)}+ Stars
                  <span className="filter-pill-close">✕</span>
                </div>
              )}
              {additionalPrefs && additionalPrefs.trim().length > 0 && (
                <div className="filter-pill" onClick={() => removeFilterPill('vibes')}>
                  <span className="filter-pill-label">Vibes:</span> {additionalPrefs.length > 20 ? additionalPrefs.substring(0, 17) + '...' : additionalPrefs}
                  <span className="filter-pill-close">✕</span>
                </div>
              )}
              
              <button className="filter-reset-btn" onClick={handleReset}>
                <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>restart_alt</span>
                Reset All
              </button>
              
              <div style={{ height: '24px', width: '1px', backgroundColor: 'var(--outline-variant)', opacity: 0.3, alignSelf: 'center', margin: '0 4px' }}></div>
              
              <div className="filter-static-pill" onClick={() => {
                setAdditionalPrefs(prev => prev ? prev + ", pet friendly" : "pet friendly");
                setTimeout(() => handleSearch(), 50);
              }}>Pet Friendly</div>
              <div className="filter-static-pill" onClick={() => {
                setAdditionalPrefs(prev => prev ? prev + ", outdoor seating" : "outdoor seating");
                setTimeout(() => handleSearch(), 50);
              }}>Outdoor Seating</div>
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
              <h2 className="font-display-lg" style={{ fontSize: '32px', color: 'var(--on-background)', margin: 0 }}>
                {recommendations.summary || "Your Top recommendations:"}
              </h2>
              <button className="btn-primary" style={{ width: 'auto', padding: '10px 20px' }} onClick={handleReset}>
                🔄 Start New Search
              </button>
            </div>

            {recommendations.used_fallback && (
              <div className="status-badge status-offline" style={{ display: 'flex', width: '100%', marginBottom: '20px' }}>
                ⚠️ The AI reasoning server was offline or busy. Showing rating-sorted matching restaurants.
              </div>
            )}

            {/* Community Insights Chart */}
            {chartStats && (
              <div className="glass-panel insights-card" style={{ marginBottom: '32px' }}>
                <div className="insights-header">
                  <h3 className="insights-title">Neighborhood Community Ratings</h3>
                  <div className="insights-avg">
                    <span className="star">★</span>
                    <span className="score">{chartStats.avg.toFixed(1)}</span>
                    <span className="count">({chartStats.total} matches in pool)</span>
                  </div>
                </div>
                
                <div className="rating-chart-container">
                  {([5, 4, 3, 2, 1] as const).map((star) => {
                    const count = chartStats.dist[star];
                    const heightPercent = (count / chartStats.maxCount) * 100;
                    return (
                      <div key={star} className="chart-bar-col">
                        <div className="chart-tooltip">{count}</div>
                        <div 
                          className="chart-bar-bg" 
                          style={{ height: `${heightPercent}%` }}
                        >
                          <div className="chart-bar-fill"></div>
                        </div>
                        <span className="chart-label">{star}★</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Cards Grid */}
            {filteredRecommendations.length === 0 ? (
              <div className="welcome-banner">
                <div className="welcome-emoji">ℹ️</div>
                <p className="welcome-desc">No restaurants matched your specific criteria. Try adjusting the filters or search query.</p>
              </div>
            ) : (
              <div className="cards-grid">
                {filteredRecommendations.map((rec, idx) => (
                  <article key={idx} className="restaurant-card">
                    <div className="image-container">
                      <img 
                        src={getCuisineImage(rec.cuisine)} 
                        alt={rec.name} 
                        className="restaurant-image"
                      />
                      <div className="rating-badge">
                        <span className="material-symbols-outlined text-sm rating-gradient" style={{ fontVariationSettings: "'FILL' 1" }}>star</span>
                        <span className="font-bold">{rec.rating.toFixed(1)}</span>
                      </div>
                      <div className="rank-badge">#{rec.rank}</div>
                      {rec.rank === 1 && <div className="premium-badge">Premium Choice</div>}
                    </div>

                    <div className="card-details">
                      <h3 className="restaurant-name">{rec.name}</h3>
                      <div className="restaurant-location">
                        <span className="material-symbols-outlined" style={{ fontSize: '16px' }}>location_on</span>
                        <span>{rec.location}</span>
                      </div>
                      <div className="card-row">
                        <span className="cuisine-tag" style={{ display: 'flex', gap: '4px', alignItems: 'center' }}>
                          <span>{getCuisineIcon(rec.cuisine)}</span>
                          <span>{rec.cuisine}</span>
                        </span>
                        <span className="cost-badge">{rec.estimated_cost}</span>
                      </div>
                      <div className="ai-explanation">
                        {rec.explanation}
                      </div>

                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '20px', paddingTop: '12px', borderTop: '1px solid var(--outline-variant)' }}>
                        <div style={{ display: 'flex', marginLeft: '6px' }}>
                          <div style={{ width: '28px', height: '28px', borderRadius: '50%', border: '2px solid var(--surface)', backgroundColor: 'var(--surface-variant)', overflow: 'hidden', zIndex: 3 }}>
                            <img alt="User" src="https://lh3.googleusercontent.com/aida-public/AB6AXuBzIqHnqkbDq1MCPMZSkAz2ZEFLJJIS_k7H-LwvTfIiYLndOFion_9oJ1vdUVk7O8isxVLq31QDXoIuzUEz0zWfNObmr8d3-KFZVsYpE9dZ75-K-jM-3_oxFcWyYa1a57vmfmGnhVylkry88nnga4Oj1u3VXxtDpQ9Gjv1LS4HktkX0hBUpCeV_7A5VZmoTAD14s2rqkqRGNtkahtwqnKaif-GBPuedj1gI0VSkoyC2vLcaW8MfqlVJx900T771l3CmWpMd4wrAjyM" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                          </div>
                          <div style={{ width: '28px', height: '28px', borderRadius: '50%', border: '2px solid var(--surface)', backgroundColor: 'var(--surface-variant)', overflow: 'hidden', marginLeft: '-8px', zIndex: 2 }}>
                            <img alt="User" src="https://lh3.googleusercontent.com/aida-public/AB6AXuA1r1i6K8T5Kz_3mCBTRHP7qV_rE1IFL-7JyUKIv6vMCbRtixJd9zdmC2PfBfJTNpVR87V6GjK-jFhvgEKq5aKVknnNH5RBNAeQAQi6EFttXfw-hUkkJyjMdbIP8kSC1d3eiGmkafhdqfgU3YSVVjT6-O-AZGwJdkPPIxcz2-whZHARSZoLJal8UI2aBeIlEld9pUumDuKtRF3_yY8ugwdDv9NGfOMX4XIOzHQcWQRD69z6yQUIo69t1Ekpqowmn0f_ki6Qqmhlxco" style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                          </div>
                          <div style={{ width: '28px', height: '28px', borderRadius: '50%', border: '2px solid var(--surface)', backgroundColor: 'var(--outline-variant)', color: 'var(--on-surface-variant)', fontSize: '9px', fontWeight: 'bold', display: 'flex', alignItems: 'center', justifyItems: 'center', justifyContent: 'center', marginLeft: '-8px', zIndex: 1 }}>
                            +12
                          </div>
                        </div>
                        <button 
                          onClick={() => {
                            setSelectedRestaurant(rec);
                            setDrawerOpen(true);
                          }}
                          className="btn-secondary" 
                          style={{ margin: 0, padding: '8px 16px', display: 'inline-flex', width: 'auto', gap: '4px' }}
                        >
                          Expand for Details
                          <span className="material-symbols-outlined" style={{ fontSize: '18px' }}>keyboard_arrow_down</span>
                        </button>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>
        ) : wizardActive ? (
          /* ==========================================
             STEPPER PREFERENCE WIZARD
             ========================================== */
          <div className="glass-panel" style={{ maxWidth: '650px', margin: '0 auto', width: '100%' }}>
            
            {/* Progress Stepper indicator */}
            <nav style={{ marginBottom: '32px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', position: 'relative' }}>
                <div style={{ position: 'absolute', top: '20px', left: 0, right: 0, height: '2px', background: 'var(--outline-variant)', opacity: 0.3, zIndex: 0 }}></div>
                <div 
                  className="stepper-progress-line"
                  style={{ 
                    position: 'absolute', 
                    top: '20px', 
                    left: 0, 
                    height: '2px', 
                    background: 'var(--primary)', 
                    width: `${((step - 1) / 3) * 100}%`,
                    zIndex: 0 
                  }}
                ></div>

                {/* Steps circles */}
                {[1, 2, 3, 4].map((s) => {
                  const icons = ["location_on", "restaurant", "payments", "tune"];
                  const labels = ["Location", "Cuisine", "Budget", "Vibes"];
                  const isActive = step === s;
                  const isCompleted = step > s;

                  return (
                    <div key={s} style={{ zIndex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px' }}>
                      <div 
                        className="step-circle"
                        style={{
                          width: '40px',
                          height: '40px',
                          borderRadius: '50%',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          background: isActive || isCompleted ? 'var(--primary)' : 'var(--surface-variant)',
                          color: isActive || isCompleted ? 'var(--on-primary)' : 'var(--on-surface-variant)',
                          border: '2px solid transparent',
                          boxShadow: isActive ? '0 0 0 4px rgba(183, 18, 42, 0.2)' : 'none',

                          cursor: isCompleted ? 'pointer' : 'default'
                        }}
                        onClick={() => { if (isCompleted) setStep(s); }}
                      >
                        {isCompleted ? "✓" : <span style={{ fontSize: '18px' }} className="material-symbols-outlined">{icons[s-1]}</span>}
                      </div>
                      <span style={{ fontSize: '11px', fontWeight: 600, color: isActive || isCompleted ? 'var(--primary)' : 'var(--on-surface-variant)' }}>
                        {labels[s-1]}
                      </span>
                    </div>
                  );
                })}
              </div>
            </nav>

            {/* Stepper Screens */}
            <div>
              {step === 1 && (
                /* Step 1: Location selection */
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <div>
                    <h2 className="font-display-lg" style={{ fontSize: '28px', color: 'var(--primary)', marginBottom: '8px' }}>Where are we eating?</h2>
                    <p style={{ fontSize: '14px', color: 'var(--on-surface-variant)' }}>Search for a neighborhood or city (e.g. Indiranagar, Bangalore).</p>
                  </div>

                  <div className="form-group" style={{ position: 'relative' }} ref={autocompleteRef}>
                    <label className="form-label" htmlFor="loc-query">Select Neighborhood/City</label>
                    <div style={{ display: 'flex', position: 'relative', alignItems: 'center' }}>
                      <span className="material-symbols-outlined" style={{ position: 'absolute', left: '12px', color: 'var(--outline)' }}>search</span>
                      <input 
                        type="text" 
                        id="loc-query" 
                        className="form-control" 
                        style={{ paddingLeft: '40px', height: '48px' }}
                        value={locationQuery}
                        onChange={(e) => {
                          setLocationQuery(e.target.value);
                          setAutocompleteOpen(true);
                        }}
                        onFocus={() => setAutocompleteOpen(true)}
                        placeholder="Search city or neighborhood..."
                      />
                    </div>

                    {/* Autocomplete dropdown suggestions */}
                    {autocompleteOpen && suggestions.length > 0 && (
                      <div className="autocomplete-box">
                        {suggestions.map((item) => (
                          <div 
                            key={item} 
                            className="autocomplete-item"
                            onClick={() => {
                              setLocation(item);
                              setLocationQuery(item);
                              setAutocompleteOpen(false);
                            }}
                          >
                            <span>📍</span>
                            <span>{item}</span>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <button 
                    type="button" 
                    className="btn-secondary" 
                    style={{ height: '48px', margin: 0 }}
                    onClick={() => {
                      if (stats.location_options.length > 0) {
                        const defaultLoc = stats.location_options.includes("Bangalore") ? "Bangalore" : stats.location_options[0];
                        setLocation(defaultLoc);
                        setLocationQuery(defaultLoc);
                      }
                    }}
                  >
                    🎯 Use Current Default Location
                  </button>

                  <div style={{ display: 'flex', justifyContent: 'flex-end', marginTop: '16px' }}>
                    <button type="button" className="btn-primary" style={{ width: 'auto', padding: '12px 28px' }} onClick={() => setStep(2)}>
                      Next Step ➔
                    </button>
                  </div>
                </div>
              )}

              {step === 2 && (
                /* Step 2: Cravings Selection */
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <div>
                    <h2 className="font-display-lg" style={{ fontSize: '28px', color: 'var(--primary)', marginBottom: '8px' }}>What are you craving?</h2>
                    <p style={{ fontSize: '14px', color: 'var(--on-surface-variant)' }}>Pick a cuisine chip or select "Any Cuisines".</p>
                  </div>

                  <div className="cravings-grid">
                    <div 
                      className={`craving-chip ${selectedCuisine === 'Any' ? 'active' : ''}`}
                      onClick={() => setSelectedCuisine("Any")}
                    >
                      <span className="craving-icon">🍱</span>
                      <span style={{ fontSize: '12px', fontWeight: 'bold' }}>Any Cuisine</span>
                    </div>

                    {stats.cuisines.map((c) => (
                      <div 
                        key={c} 
                        className={`craving-chip ${selectedCuisine === c ? 'active' : ''}`}
                        onClick={() => setSelectedCuisine(c)}
                      >
                        <span className="craving-icon">{getCuisineIcon(c)}</span>
                        <span style={{ fontSize: '12px', fontWeight: 'bold', textAlign: 'center' }}>{c}</span>
                      </div>
                    ))}
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px' }}>
                    <button type="button" className="btn-secondary" style={{ width: 'auto', padding: '12px 24px', margin: 0 }} onClick={() => setStep(1)}>
                      Back
                    </button>
                    <button type="button" className="btn-primary" style={{ width: 'auto', padding: '12px 28px' }} onClick={() => setStep(3)}>
                      Next Step ➔
                    </button>
                  </div>
                </div>
              )}

              {step === 3 && (
                /* Step 3: Budget Range & Presets */
                <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                  <div>
                    <h2 className="font-display-lg" style={{ fontSize: '28px', color: 'var(--primary)', marginBottom: '8px' }}>Plan your spend</h2>
                    <p style={{ fontSize: '14px', color: 'var(--on-surface-variant)' }}>Set a budget tier or choose an automatic preset.</p>
                  </div>

                  {/* Budget Selector */}
                  <div className="form-group">
                    <label className="form-label">💰 Select Budget Tier</label>
                    <div className="budget-pills">
                      {stats.budget_tiers.map((tier) => (
                        <button
                          key={tier}
                          type="button"
                          className={`budget-pill ${budget === tier ? 'active' : ''}`}
                          onClick={() => {
                            setBudget(tier);
                            setSelectedPreset(null);
                          }}
                        >
                          {tier.charAt(0).toUpperCase() + tier.slice(1)}
                        </button>
                      ))}
                    </div>
                  </div>

                  {/* Preference Presets */}
                  <div>
                    <label className="form-label">✨ Quick Preference Presets</label>
                    <div className="presets-grid">
                      {/* Date Night */}
                      <div 
                        className={`preset-card ${selectedPreset === 'datenight' ? 'active' : ''}`}
                        onClick={() => handlePresetSelect('datenight')}
                      >
                        <img 
                          src="https://images.unsplash.com/photo-1522336572241-99a370df74e5?w=200&h=150&fit=crop" 
                          alt="Date Night" 
                          className="preset-image"
                        />
                        <div className="preset-overlay">
                          <span className="preset-label">Date Night</span>
                        </div>
                        {selectedPreset === 'datenight' && <div className="preset-check">✓</div>}
                      </div>

                      {/* Quick Lunch */}
                      <div 
                        className={`preset-card ${selectedPreset === 'quicklunch' ? 'active' : ''}`}
                        onClick={() => handlePresetSelect('quicklunch')}
                      >
                        <img 
                          src="https://images.unsplash.com/photo-1543007630-9710e4a00a20?w=200&h=150&fit=crop" 
                          alt="Quick Lunch" 
                          className="preset-image"
                        />
                        <div className="preset-overlay">
                          <span className="preset-label">Quick Lunch</span>
                        </div>
                        {selectedPreset === 'quicklunch' && <div className="preset-check">✓</div>}
                      </div>

                      {/* Family Dinner */}
                      <div 
                        className={`preset-card ${selectedPreset === 'familydinner' ? 'active' : ''}`}
                        onClick={() => handlePresetSelect('familydinner')}
                      >
                        <img 
                          src="https://images.unsplash.com/photo-1511795409834-ef04bbd61622?w=200&h=150&fit=crop" 
                          alt="Family Dinner" 
                          className="preset-image"
                        />
                        <div className="preset-overlay">
                          <span className="preset-label">Family Dinner</span>
                        </div>
                        {selectedPreset === 'familydinner' && <div className="preset-check">✓</div>}
                      </div>
                    </div>
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px' }}>
                    <button type="button" className="btn-secondary" style={{ width: 'auto', padding: '12px 24px', margin: 0 }} onClick={() => setStep(2)}>
                      Back
                    </button>
                    <button type="button" className="btn-primary" style={{ width: 'auto', padding: '12px 28px' }} onClick={() => setStep(4)}>
                      Next Step ➔
                    </button>
                  </div>
                </div>
              )}

              {step === 4 && (
                /* Step 4: Rating, Vibes, and Top K */
                <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                  <div>
                    <h2 className="font-display-lg" style={{ fontSize: '28px', color: 'var(--primary)', marginBottom: '8px' }}>Refine details</h2>
                    <p style={{ fontSize: '14px', color: 'var(--on-surface-variant)' }}>Set final thresholds and describe your vibe.</p>
                  </div>

                  {/* Rating Slider */}
                  <div className="form-group">
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <label className="form-label" style={{ margin: 0 }}>⭐ Minimum Rating</label>
                      <span style={{ fontSize: '13px', fontWeight: 'bold', color: 'var(--primary)' }}>
                        {minRating.toFixed(1)} ★
                      </span>
                    </div>
                    <input
                      type="range"
                      min="0"
                      max="5"
                      step="0.1"
                      className="form-control"
                      style={{ padding: 0, height: '6px', cursor: 'pointer' }}
                      value={minRating}
                      onChange={(e) => {
                        setMinRating(parseFloat(e.target.value));
                        setSelectedPreset(null);
                      }}
                    />
                  </div>

                  {/* Vibes textarea */}
                  <div className="form-group">
                    <label className="form-label" htmlFor="additional-prefs">✍️ Additional Vibes & Custom Cuisine</label>
                    <textarea
                      id="additional-prefs"
                      className="form-control"
                      style={{ minHeight: '80px', resize: 'vertical' }}
                      placeholder="e.g., rooftop, live music, family friendly, dessert, spicy food"
                      value={additionalPrefs}
                      onChange={(e) => {
                        setAdditionalPrefs(e.target.value);
                        setSelectedPreset(null);
                      }}
                    />
                  </div>

                  {/* Top K recommendations */}
                  <div className="form-group">
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                      <label className="form-label" style={{ margin: 0 }}>🔢 Suggestion Count</label>
                      <span style={{ fontSize: '13px', fontWeight: 'bold', color: 'var(--primary)' }}>{topK}</span>
                    </div>
                    <input
                      type="range"
                      min="1"
                      max="10"
                      step="1"
                      className="form-control"
                      style={{ padding: 0, height: '6px', cursor: 'pointer' }}
                      value={topK}
                      onChange={(e) => setTopK(parseInt(e.target.value))}
                    />
                  </div>

                  <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '16px' }}>
                    <button type="button" className="btn-secondary" style={{ width: 'auto', padding: '12px 24px', margin: 0 }} onClick={() => setStep(3)}>
                      Back
                    </button>
                    <button type="button" className="btn-primary" style={{ width: 'auto', padding: '12px 28px' }} onClick={() => handleSearch()}>
                      Find Matches ✨
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* ==========================================
             WELCOME LANDING SCREEN (BENTO GRID STYLE)
             ========================================== */
          <div style={{ display: 'flex', flexDirection: 'column', gap: '48px' }}>
            {/* Hero Spread Banner */}
            <section style={{ 
              position: 'relative', 
              minHeight: '60vh', 
              borderRadius: '24px', 
              overflow: 'hidden', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              padding: '40px 20px',
              boxShadow: '0 4px 20px rgba(0,0,0,0.08)'
            }}>
              <div 
                className="hero-bg" 
                style={{ 
                  position: 'absolute', 
                  inset: 0, 
                  backgroundImage: `linear-gradient(rgba(0,0,0,0.4), rgba(0,0,0,0.4)), url("https://images.unsplash.com/photo-1504674900247-0877df9cc836?w=1200&q=80")`,
                  backgroundSize: 'cover',
                  backgroundPosition: 'center',
                  filter: 'blur(3px)',
                  transform: 'scale(1.05)',
                  zIndex: 0
                }}
              ></div>

              <div className="glass-panel animate-float" style={{ position: 'relative', zIndex: 1, maxWidth: '600px', textAlign: 'center', padding: '40px' }}>
                <div style={{ fontSize: '56px', marginBottom: '16px' }}>🍕</div>
                <h1 className="font-display-lg" style={{ fontSize: '42px', color: 'var(--primary)', marginBottom: '12px', lineHeight: 1.2 }}>
                  Discover Your Next Favorite Meal
                </h1>
                <p style={{ fontSize: '16px', color: 'var(--on-surface-variant)', marginBottom: '32px', lineHeight: 1.5 }}>
                  Hyper-personalized restaurant recommendations powered by Zomato dataset & AI reasoning. Tailored to your exact neighborhood, taste, and budget.
                </p>
                <div style={{ display: 'flex', gap: '16px', justifyContent: 'center', flexWrap: 'wrap' }}>
                  <button 
                    onClick={() => {
                      setWizardActive(true);
                      setStep(1);
                    }}
                    className="btn-primary" 
                    style={{ width: 'auto', padding: '14px 32px', borderRadius: '30px' }}
                  >
                    Start Discovering
                  </button>
                  <button 
                    onClick={() => {
                      setLocation("Bangalore");
                      setBudget("medium");
                      setSelectedCuisine("Any");
                      setMinRating(4.0);
                      setAdditionalPrefs("family friendly, quick service");
                      setTopK(3);
                      // Trigger search immediately
                      setLoading(true);
                      setTimeout(() => {
                        handleSearch();
                      }, 200);
                    }}
                    className="btn-secondary" 
                    style={{ width: 'auto', padding: '14px 32px', borderRadius: '30px', margin: 0 }}
                  >
                    Surprise Me
                  </button>
                </div>
              </div>
            </section>

            {/* How CraveAI works process cards */}
            <section style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
              <div style={{ textAlign: 'center' }}>
                <h2 className="font-display-lg" style={{ fontSize: '28px', color: 'var(--on-background)' }}>How CraveAI Works</h2>
                <div style={{ width: '64px', height: '4px', background: 'var(--primary)', margin: '8px auto', borderRadius: '2px' }}></div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '24px' }}>
                {/* Step 1 */}
                <div className="glass-panel" style={{ borderLeft: '4px solid var(--primary)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="step-number font-display-lg" style={{ fontSize: '42px', opacity: 0.3 }}>01</span>
                    <span style={{ fontSize: '28px', color: 'var(--primary)' }}>📍</span>
                  </div>
                  <h3 className="font-display-lg" style={{ fontSize: '20px', color: 'var(--primary)' }}>Analyze</h3>
                  <p style={{ fontSize: '14px', color: 'var(--on-surface-variant)', lineHeight: 1.4 }}>
                    Define your exact city neighborhood or area. We validate and filter locations to match local regions dynamically.
                  </p>
                </div>

                {/* Step 2 */}
                <div className="glass-panel" style={{ borderLeft: '4px solid var(--primary-container)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="step-number font-display-lg" style={{ fontSize: '42px', opacity: 0.3 }}>02</span>
                    <span style={{ fontSize: '28px', color: 'var(--primary)' }}>🍱</span>
                  </div>
                  <h3 className="font-display-lg" style={{ fontSize: '20px', color: 'var(--primary)' }}>Filter</h3>
                  <p style={{ fontSize: '14px', color: 'var(--on-surface-variant)', lineHeight: 1.4 }}>
                    Apply deterministic filters across cuisines, ratings, and price tiers, narrowing the pool down to a bounded candidate list.
                  </p>
                </div>

                {/* Step 3 */}
                <div className="glass-panel" style={{ borderLeft: '4px solid var(--outline)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span className="step-number font-display-lg" style={{ fontSize: '42px', opacity: 0.3 }}>03</span>
                    <span style={{ fontSize: '28px', color: 'var(--primary)' }}>✨</span>
                  </div>
                  <h3 className="font-display-lg" style={{ fontSize: '20px', color: 'var(--primary)' }}>Recommend</h3>
                  <p style={{ fontSize: '14px', color: 'var(--on-surface-variant)', lineHeight: 1.4 }}>
                    The AI parses options and ranks restaurants, providing clear explanations of why they match your preferences.
                  </p>
                </div>
              </div>
            </section>

            {/* Bento Highlight Grid */}
            <section style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '20px' }}>
              {/* Premium Choice card */}
              <div 
                className="glass-panel" 
                style={{ 
                  gridColumn: 'span 2', 
                  position: 'relative', 
                  overflow: 'hidden', 
                  minHeight: '260px',
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'flex-end',
                  padding: '24px'
                }}
              >
                <div style={{
                  position: 'absolute',
                  inset: 0,
                  backgroundImage: `linear-gradient(rgba(0,0,0,0.3), rgba(0,0,0,0.6)), url("https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=600&fit=crop")`,
                  backgroundSize: 'cover',
                  backgroundPosition: 'center',
                  zIndex: 0
                }}></div>
                <div style={{ position: 'relative', zIndex: 1 }}>
                  <span style={{ background: 'var(--primary)', color: 'white', padding: '4px 12px', borderRadius: '8px', fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                    Premium Selection
                  </span>
                  <h3 className="font-display-lg" style={{ fontSize: '28px', color: 'white', marginTop: '12px', marginBottom: '8px' }}>Curated Dining</h3>
                  <p style={{ fontSize: '14px', color: 'rgba(255,255,255,0.9)', maxWidth: '400px' }}>
                    From cozy hidden local neighborhood bistros to premium dining choices with high ratings.
                  </p>
                </div>
              </div>

              {/* Match Score stat box */}
              <div className="glass-panel" style={{ background: 'var(--primary)', color: 'var(--on-primary)', display: 'flex', flexDirection: 'column', justifyContent: 'center', alignItems: 'center', textAlign: 'center', padding: '24px' }}>
                <span className="material-symbols-outlined" style={{ fontSize: '48px', marginBottom: '12px', fontVariationSettings: "'FILL' 1" }}>auto_awesome</span>
                <h4 className="font-display-lg" style={{ fontSize: '24px', marginBottom: '4px' }}>98% Match</h4>
                <p style={{ fontSize: '12px', opacity: 0.8 }}>Our users find perfect dining suggestions instantly without scrolling.</p>
              </div>

              {/* Global Cuisines card */}
              <div className="glass-panel" style={{ position: 'relative', overflow: 'hidden', minHeight: '260px', display: 'flex', alignItems: 'flex-end', padding: '24px' }}>
                <div style={{
                  position: 'absolute',
                  inset: 0,
                  backgroundImage: `linear-gradient(rgba(0,0,0,0.2), rgba(0,0,0,0.6)), url("https://images.unsplash.com/photo-1563245372-f21724e3856d?w=400&fit=crop")`,
                  backgroundSize: 'cover',
                  backgroundPosition: 'center',
                  zIndex: 0
                }}></div>
                <div style={{ position: 'relative', zIndex: 1 }}>
                  <span style={{ color: 'white', fontSize: '12px', fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: '1px' }}>Global Taste</span>
                  <h3 className="font-display-lg" style={{ fontSize: '20px', color: 'white', marginTop: '4px' }}>Cuisines Coverage</h3>
                </div>
              </div>
            </section>
          </div>
        )}
      </div>

      {/* Expandable Drawer Modal */}
      <div 
        className={`drawer-overlay ${drawerOpen ? 'open' : ''}`}
        onClick={() => setDrawerOpen(false)}
      ></div>
      <div className={`detail-drawer ${drawerOpen ? 'open' : ''}`}>
        {selectedRestaurant && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{ background: 'var(--primary)', color: 'white', padding: '4px 12px', borderRadius: '8px', fontSize: '11px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                  #{selectedRestaurant.rank} Rank
                </span>
                <h2 className="font-display-lg" style={{ fontSize: '28px', color: 'var(--on-background)', marginTop: '8px', marginBottom: '4px' }}>
                  {selectedRestaurant.name}
                </h2>
                <p style={{ fontSize: '14px', color: 'var(--on-surface-variant)', display: 'flex', gap: '4px', alignItems: 'center' }}>
                  <span>📍</span> <span>{selectedRestaurant.location}</span>
                </p>
              </div>
              <button 
                onClick={() => setDrawerOpen(false)}
                style={{ background: 'none', border: 'none', fontSize: '24px', cursor: 'pointer', color: 'var(--outline)' }}
              >
                ✕
              </button>
            </div>

            {/* Redesigned Hero Banner Image in Drawer */}
            <div className="drawer-hero-banner">
              <img 
                src={getCuisineImage(selectedRestaurant.cuisine)} 
                alt={selectedRestaurant.name} 
                className="drawer-hero-img"
              />
              <div className="drawer-hero-overlay">
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span className="drawer-tag">Top Rated</span>
                  <span className="drawer-tag" style={{ backgroundColor: 'var(--primary)' }}>
                    {selectedRestaurant.metadata?.rest_type || 'Modern Bistro'}
                  </span>
                </div>
              </div>
            </div>

            {/* AI Insights block */}
            <div className="ai-insights-panel">
              <div className="ai-insights-header">
                <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>smart_toy</span>
                <h3 className="ai-insights-title">AI Insights & Match Reason</h3>
              </div>
              <p style={{ fontSize: '14px', lineHeight: 1.5, color: 'var(--on-surface-variant)' }}>
                {selectedRestaurant.explanation}
              </p>
              <div className="bento-stats-grid">
                <div className="bento-stat-card">
                  <span className="bento-stat-val">
                    {selectedRestaurant.rating >= 4.5 ? '98%' : selectedRestaurant.rating >= 4.0 ? '92%' : '85%'}
                  </span>
                  <span className="bento-stat-lbl">Match Score</span>
                </div>
                <div className="bento-stat-card">
                  <span className="bento-stat-val">
                    {selectedRestaurant.rating >= 4.5 ? 'High' : 'Medium'}
                  </span>
                  <span className="bento-stat-lbl">Intensity</span>
                </div>
                <div className="bento-stat-card">
                  <span className="bento-stat-val">
                    {selectedRestaurant.budget_tier === 'high' ? '$$$' : selectedRestaurant.budget_tier === 'medium' ? '$$' : '$'}
                  </span>
                  <span className="bento-stat-lbl">Price Tier</span>
                </div>
              </div>
            </div>

            {/* Neighborhood Flavor Map Conic Viz */}
            <div className="glass-panel" style={{ padding: '16px' }}>
              <h3 className="font-display-lg" style={{ fontSize: '18px', marginBottom: '16px' }}>Neighborhood Flavor Map</h3>
              <div className="flavor-map-grid">
                <div className="conic-chart-wrapper">
                  <div className="cuisine-pie" style={{ width: '100%', height: '100%' }}></div>
                  <div className="conic-chart-donut">
                    <div className="donut-text">
                      <span className="donut-lbl" style={{ display: 'block', fontSize: '10px', color: 'var(--primary)', fontWeight: 'bold' }}>Local</span>
                      <span className="donut-lbl" style={{ display: 'block' }}>Trends</span>
                    </div>
                  </div>
                </div>
                <div className="flavor-legend">
                  <div className="legend-item">
                    <div className="legend-color-label">
                      <div className="legend-color-dot" style={{ backgroundColor: 'var(--primary)' }}></div>
                      <span>{selectedRestaurant.cuisine.split(',')[0]}</span>
                    </div>
                    <strong>45%</strong>
                  </div>
                  <div className="legend-item">
                    <div className="legend-color-label">
                      <div className="legend-color-dot" style={{ backgroundColor: '#de2656' }}></div>
                      <span>Asian Fusion</span>
                    </div>
                    <strong>25%</strong>
                  </div>
                  <div className="legend-item">
                    <div className="legend-color-label">
                      <div className="legend-color-dot" style={{ backgroundColor: '#e4bebc' }}></div>
                      <span>Artisanal Cafe</span>
                    </div>
                    <strong>15%</strong>
                  </div>
                  <div className="legend-item">
                    <div className="legend-color-label">
                      <div className="legend-color-dot" style={{ backgroundColor: '#8f6f6e' }}></div>
                      <span>Other</span>
                    </div>
                    <strong>15%</strong>
                  </div>
                </div>
              </div>
            </div>

            {/* Static District Map/Address */}
            <div className="glass-panel" style={{ padding: '16px' }}>
              <h3 className="font-display-lg" style={{ fontSize: '16px', marginBottom: '12px' }}>Location & Timing</h3>
              <div style={{ borderRadius: '12px', overflow: 'hidden', height: '120px', position: 'relative', marginBottom: '12px' }}>
                <img 
                  src="https://images.unsplash.com/photo-1524661135-423995f22d0b?w=600&h=300&fit=crop" 
                  alt="Neighborhood Map"
                  style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                />
                <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', background: 'var(--primary)', width: '12px', height: '12px', borderRadius: '50%', border: '2px solid white', boxShadow: '0 0 0 8px rgba(183, 18, 42, 0.3)' }}></div>
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px', fontSize: '13px' }}>
                {selectedRestaurant.metadata?.address && (
                  <div style={{ display: 'flex', gap: '8px' }}>
                    <span>📍</span>
                    <span>{selectedRestaurant.metadata.address}</span>
                  </div>
                )}
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span>⏰</span>
                  <span>Open Now · 11:30 AM - 11:00 PM</span>
                </div>
                <div style={{ display: 'flex', gap: '8px' }}>
                  <span>🍽️</span>
                  <span>{selectedRestaurant.metadata?.rest_type || 'Dining · Table Service'}</span>
                </div>
              </div>
            </div>

            {/* Community Rating Chart in Drawer */}
            <div className="glass-panel" style={{ padding: '16px' }}>
              <h3 className="font-display-lg" style={{ fontSize: '16px', marginBottom: '12px' }}>Community Ratings</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                {[5, 4, 3, 2, 1].map(stars => {
                  const widths = { 5: '85%', 4: '10%', 3: '3%', 2: '1%', 1: '1%' };
                  return (
                    <div key={stars} style={{ display: 'flex', alignItems: 'center', gap: '12px', fontSize: '12px' }}>
                      <span style={{ width: '24px', fontWeight: 'bold' }}>{stars} ★</span>
                      <div style={{ flexGrow: 1, height: '8px', backgroundColor: 'var(--surface-variant)', borderRadius: '4px', overflow: 'hidden' }}>
                        <div style={{ height: '100%', width: widths[stars as keyof typeof widths], backgroundColor: 'var(--primary)' }}></div>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Actions footer */}
            <div className="drawer-actions-footer">
              <button 
                type="button" 
                className="btn-secondary" 
                style={{ flex: 1, margin: 0, padding: '12px' }}
                onClick={() => {
                  alert(`Added ${selectedRestaurant.name} to favorites!`);
                }}
              >
                ❤️ Favorite
              </button>
              <button 
                type="button" 
                className="btn-secondary" 
                style={{ flex: 1, margin: 0, padding: '12px' }}
                onClick={() => {
                  alert(`Sharing ${selectedRestaurant.name}...`);
                }}
              >
                🔗 Share
              </button>
              <button 
                type="button" 
                className="btn-primary" 
                style={{ flex: 2, padding: '12px' }}
                onClick={() => {
                  const url = selectedRestaurant.metadata?.url || `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(selectedRestaurant.name + ' ' + selectedRestaurant.location)}`;
                  window.open(url, '_blank');
                }}
              >
                🗺️ Get Directions
              </button>
            </div>
          </div>
        )}
      </div>

      {/* Floating Filter FAB */}
      {(recommendations || error) && (
        <button 
          className="floating-filter-fab"
          onClick={() => {
            setWizardActive(true);
            setRecommendations(null);
            setError(null);
          }}
        >
          <span className="material-symbols-outlined">filter_list</span>
          <span>Filters</span>
          <div className="floating-filter-badge">
            {getActiveFiltersCount()}
          </div>
        </button>
      )}

      {/* Persistent Bottom Navigation */}
      <footer className="bottom-nav">
        <div className={`nav-item ${!wizardActive && !recommendations ? 'active' : ''}`} onClick={handleReset}>
          <span className="nav-icon">🏠</span>
          <span className="nav-label">Home</span>
        </div>
        <div className={`nav-item ${wizardActive ? 'active' : ''}`} onClick={() => {
          setWizardActive(true);
          setRecommendations(null);
        }}>
          <span className="nav-icon">🔍</span>
          <span className="nav-label">Search</span>
        </div>
        <div className="nav-item" onClick={() => alert("Favorites feature is coming soon!")}>
          <span className="nav-icon">❤️</span>
          <span className="nav-label">Favorites</span>
        </div>
        <div className="nav-item" onClick={() => alert("AI assistant chat is coming soon!")}>
          <span className="nav-icon">🤖</span>
          <span className="nav-label">AI Chat</span>
        </div>
      </footer>
    </div>
  );
}
