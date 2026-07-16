"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { getAuthHeader } from "@/lib/supabase";
import { 
  MapPin, Navigation, Compass, Plus, Info, 
  ArrowLeft, Eye, CheckCircle2, ChevronRight, UploadCloud, Trash2
} from "lucide-react";

export default function PostPropertyPage() {
  const router = useRouter();
  
  // Cities/Areas dynamic dropdowns state
  const [citiesData, setCitiesData] = useState<any[]>([]);
  
  // Form Step State
  const [currentStep, setCurrentStep] = useState(1);
  const totalSteps = 3;
  const stepTitles = ["Property Details", "Upload Media", "Amenities & Rules"];

  // Form Field States
  const [title, setTitle] = useState("");
  const [cityId, setCityId] = useState("");
  const [areaId, setAreaId] = useState("");
  const [price, setPrice] = useState("");
  const [deposit, setDeposit] = useState("");
  const [type, setType] = useState("1BHK");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [facilities, setFacilities] = useState<string[]>([]);
  const [description, setDescription] = useState("");
  const [exactLocation, setExactLocation] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");

  // Rules states
  const [petsAllowed, setPetsAllowed] = useState(false);
  const [noSmoking, setNoSmoking] = useState(true);
  const [foodPreference, setFoodPreference] = useState("Any");
  const [curfew, setCurfew] = useState("No Curfew");
  const [visitors, setVisitors] = useState("Allowed");
  const [availableFrom, setAvailableFrom] = useState("Immediately");
  
  // Image files state
  const [mainImage, setMainImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  
  // Form Status States
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState("");
  const [error, setError] = useState("");

  // Location Tab State: "manual" vs "gps"
  const [locationTab, setLocationTab] = useState<"manual" | "gps">("manual");
  const [gpsStatus, setGpsStatus] = useState("");
  
  // Ref for manual address textarea focus
  const addressTextareaRef = useRef<HTMLTextAreaElement>(null);

  // Fetch Cities and Areas
  useEffect(() => {
    fetch("/api/cities-areas/")
      .then((res) => res.json())
      .then((data) => {
        if (Array.isArray(data)) {
          setCitiesData(data);
          if (data.length > 0) {
            setCityId(data[0].id.toString());
          }
        }
      })
      .catch((err) => console.error("Error loading cities:", err));
  }, []);

  const activeCity = citiesData.find((c) => c.id.toString() === cityId);
  const areasList = activeCity ? activeCity.areas : [];

  useEffect(() => {
    if (areasList.length > 0) {
      setAreaId(areasList[0].id.toString());
    } else {
      setAreaId("");
    }
  }, [cityId, citiesData]);

  // GPS Geolocation Handler
  const handleDetectGPS = () => {
    setGpsStatus("Detecting satellite signals...");
    if (!navigator.geolocation) {
      setGpsStatus("Geolocation is not supported by your browser.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const lat = position.coords.latitude.toFixed(6);
        const lng = position.coords.longitude.toFixed(6);
        
        setLatitude(lat);
        setLongitude(lng);

        // Generate Google Maps link
        const mapsLink = `https://www.google.com/maps?q=${lat},${lng}`;
        setExactLocation(mapsLink);
        setGpsStatus(`Coordinates detected: Lat ${lat}, Lng ${lng}. Maps link generated!`);
        
        // Timeout to switch tab and focus
        setTimeout(() => {
          setLocationTab("manual");
          if (addressTextareaRef.current) {
            addressTextareaRef.current.focus();
          }
        }, 1200);
      },
      (err) => {
        setGpsStatus(`Satellite detection failed: ${err.message}. Please enter address manually.`);
      },
      { enableHighAccuracy: true, timeout: 8000 }
    );
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0] || null;
    setMainImage(file);
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    } else {
      setImagePreview(null);
    }
  };

  const handleAmenityToggle = (amenity: string) => {
    if (facilities.includes(amenity)) {
      setFacilities(facilities.filter(item => item !== amenity));
    } else {
      setFacilities([...facilities, amenity]);
    }
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    const authHeader = await getAuthHeader();
    if (!authHeader) {
      router.push("/login");
      return;
    }

    try {
      const formData = new FormData();
      formData.append("title", title);
      formData.append("city", cityId);
      formData.append("area", areaId);
      formData.append("location", activeCity?.name || "Mysore");
      formData.append("price", price);
      formData.append("deposit", deposit);
      formData.append("type", type);
      formData.append("phone", phone);
      formData.append("address", address);
      
      // Facilities string format
      const facilitiesStr = facilities.length > 0 ? facilities.join(", ") : "WiFi";
      formData.append("facilities", facilitiesStr);
      
      formData.append("description", description);
      formData.append("exact_location", exactLocation);
      formData.append("latitude", latitude);
      formData.append("longitude", longitude);
      formData.append("available_from", availableFrom);
      formData.append("food_preference", foodPreference);
      formData.append("curfew", curfew);
      formData.append("visitors", visitors);
      
      if (mainImage) {
        formData.append("image", mainImage);
      }

      const response = await fetch("/api/listings/", {
        method: "POST",
        headers: {
          "Authorization": authHeader
        },
        body: formData
      });

      const resData = await response.json();
      if (resData.success) {
        setSuccess("Property listed successfully! Redirecting...");
        setTimeout(() => {
          router.push(`/listing/${resData.id}`);
        }, 1500);
      } else {
        setError(resData.error || "Failed to submit property.");
        setLoading(false);
      }
    } catch (err: any) {
      setError("An unexpected error occurred during submission.");
      setLoading(false);
    }
  };

  const nextStep = () => {
    // Basic validation per step
    if (currentStep === 1) {
      if (!title || !price || !deposit || !phone || !address) {
        setError("Please fill out all required fields.");
        return;
      }
    } else if (currentStep === 2) {
      if (!mainImage) {
        setError("Please upload at least the main property photo.");
        return;
      }
    }
    setError("");
    setCurrentStep(prev => Math.min(prev + 1, totalSteps));
  };

  const prevStep = () => {
    setError("");
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const progressPercentage = (currentStep / totalSteps) * 100;

  return (
    <div className="max-w-3xl mx-auto px-6 md:px-10 py-12 w-full flex-1 flex flex-col min-h-screen">
      {/* Progress Header */}
      <div className="mb-12">
        <div className="flex justify-between items-end mb-4">
          <div>
            <span className="text-xs font-bold text-primary uppercase tracking-widest">Listing Process</span>
            <h2 className="text-2xl md:text-3xl font-extrabold font-plus-jakarta text-on-surface mt-1">List Your Property</h2>
          </div>
          <div className="text-right">
            <span className="text-xs font-bold text-primary">Step {currentStep} of {totalSteps}</span>
            <p className="text-sm font-semibold text-on-surface-variant mt-0.5">{stepTitles[currentStep - 1]}</p>
          </div>
        </div>
        {/* Progress Bar */}
        <div className="h-2 w-full bg-surface-container rounded-full overflow-hidden shadow-inner">
          <div className="h-full bg-primary transition-all duration-500 ease-out" style={{ width: `${progressPercentage}%` }}></div>
        </div>
      </div>

      <div className="bg-white border border-outline-variant rounded-2xl p-6 md:p-8 shadow-md">
        <form onSubmit={handleFormSubmit} className="space-y-8">
          
          {/* STEP 1: Basic Details */}
          {currentStep === 1 && (
            <section className="space-y-6 animate-fadeIn">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="col-span-full">
                  <label className="block text-xs font-bold text-on-surface mb-2">Property Title *</label>
                  <input
                    type="text"
                    placeholder="e.g. Spacious 2BHK Flat in Indiranagar"
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                    required
                  />
                  <p className="mt-1 text-[10px] text-text-muted">A catchy title helps your property stand out.</p>
                </div>

                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">Stay Type *</label>
                  <select
                    value={type}
                    onChange={(e) => setType(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs font-semibold focus:outline-none"
                  >
                    <option value="1BHK">1 BHK Flat</option>
                    <option value="2BHK">2 BHK Flat</option>
                    <option value="3BHK">3 BHK Flat</option>
                    <option value="Single Room">Single Room</option>
                    <option value="PG (Men)">PG (Men)</option>
                    <option value="PG (Women)">PG (Women)</option>
                    <option value="Co-living">Co-living</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">Contact Phone *</label>
                  <input
                    type="text"
                    placeholder="Owner Mobile Number"
                    value={phone}
                    onChange={(e) => setPhone(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">City *</label>
                  <select
                    value={cityId}
                    onChange={(e) => setCityId(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs font-semibold focus:outline-none"
                  >
                    {citiesData.map((c) => (
                      <option key={c.id} value={c.id.toString()}>{c.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">Area / Locality *</label>
                  <select
                    value={areaId}
                    onChange={(e) => setAreaId(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs font-semibold focus:outline-none"
                    disabled={areasList.length === 0}
                  >
                    {areasList.map((a: any) => (
                      <option key={a.id} value={a.id.toString()}>{a.name}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">Rent / Month (₹) *</label>
                  <input
                    type="number"
                    placeholder="Rent Amount"
                    value={price}
                    onChange={(e) => setPrice(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                    required
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-on-surface-variant mb-2">Security Deposit (₹) *</label>
                  <input
                    type="number"
                    placeholder="Refundable Deposit"
                    value={deposit}
                    onChange={(e) => setDeposit(e.target.value)}
                    className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                    required
                  />
                </div>
              </div>

              {/* Dual Location Tabs */}
              <div className="border border-outline-variant rounded-xl overflow-hidden shadow-sm mt-6">
                <div className="flex bg-surface-container border-b border-outline-variant/30 text-xs font-bold text-on-surface-variant">
                  <button
                    type="button"
                    onClick={() => setLocationTab("manual")}
                    className={`w-1/2 py-3 text-center transition-all ${
                      locationTab === "manual" ? "bg-white text-primary border-b-2 border-primary" : "hover:bg-white/50"
                    }`}
                  >
                    Enter Address
                  </button>
                  <button
                    type="button"
                    onClick={() => setLocationTab("gps")}
                    className={`w-1/2 py-3 text-center transition-all flex items-center justify-center gap-1.5 ${
                      locationTab === "gps" ? "bg-white text-primary border-b-2 border-primary" : "hover:bg-white/50"
                    }`}
                  >
                    <Compass className="w-4 h-4 text-primary" /> Live GPS Location
                  </button>
                </div>

                <div className="p-4 bg-white">
                  {locationTab === "manual" ? (
                    <div>
                      <textarea
                        ref={addressTextareaRef}
                        rows={4}
                        placeholder="Enter full physical address (house number, block, street, landmark)..."
                        value={address}
                        onChange={(e) => setAddress(e.target.value)}
                        className="w-full border-none focus:ring-0 text-xs text-on-surface focus:outline-none placeholder:text-outline-variant"
                        required
                      />
                      {latitude && longitude && (
                        <div className="mt-2 text-[10px] text-primary font-bold flex items-center gap-1">
                          <MapPin className="w-3.5 h-3.5 fill-primary text-white" /> Attached coordinates: {latitude}, {longitude}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-6">
                      <button
                        type="button"
                        onClick={handleDetectGPS}
                        className="px-6 py-3 bg-primary text-white rounded-xl text-xs font-bold inline-flex items-center gap-2 hover:opacity-90 active:scale-95 transition-all shadow-md shadow-primary/10"
                      >
                        <Navigation className="w-4 h-4" /> Detect Coordinates
                      </button>
                      {gpsStatus && <p className="text-[11px] font-medium text-on-surface-variant mt-4">{gpsStatus}</p>}
                    </div>
                  )}
                </div>
              </div>
            </section>
          )}

          {/* STEP 2: Upload Media */}
          {currentStep === 2 && (
            <section className="space-y-6 animate-fadeIn">
              <div className="border-2 border-dashed border-outline-variant rounded-2xl p-8 text-center bg-surface-container-low hover:bg-surface-container/50 transition-colors cursor-pointer relative">
                <input
                  type="file"
                  accept="image/*"
                  onChange={handleImageChange}
                  className="absolute inset-0 opacity-0 cursor-pointer"
                />
                <div className="flex flex-col items-center gap-3 text-on-surface-variant">
                  <UploadCloud className="w-12 h-12 text-primary" />
                  <h3 className="text-sm font-bold">Upload Main Property Photo *</h3>
                  <span className="text-xs text-text-muted">{mainImage ? mainImage.name : "Drag and drop your file here, or click to browse"}</span>
                  <span className="text-[9px] uppercase tracking-wider text-text-muted">WebP, PNG, JPG (Max 10MB)</span>
                </div>
              </div>

              {imagePreview && (
                <div className="mt-6">
                  <h4 className="text-xs font-bold text-on-surface-variant mb-3">Photo Preview</h4>
                  <div className="relative w-48 h-48 rounded-2xl overflow-hidden shadow-md group border border-outline-variant">
                    <img src={imagePreview} alt="Property Preview" className="w-full h-full object-cover" />
                    <button 
                      type="button"
                      onClick={() => { setMainImage(null); setImagePreview(null); }}
                      className="absolute top-2 right-2 p-1.5 bg-error text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity shadow-md"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              )}
            </section>
          )}

          {/* STEP 3: Amenities & Rules */}
          {currentStep === 3 && (
            <section className="space-y-6 animate-fadeIn">
              {/* Amenities */}
              <div>
                <h3 className="text-xs font-bold text-primary uppercase mb-4 tracking-wider">Standard Amenities</h3>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {[
                    "WiFi Included", "Air Conditioning", "In-unit Laundry", 
                    "Parking (Car/Bike)", "Gym Access", "Full Kitchen"
                  ].map((amenity) => (
                    <button
                      type="button"
                      key={amenity}
                      onClick={() => handleAmenityToggle(amenity)}
                      className={`flex items-center gap-3 p-4 border rounded-xl cursor-pointer hover:bg-surface-container-low transition-all text-left ${
                        facilities.includes(amenity)
                          ? "border-primary bg-primary/5 text-primary font-bold shadow-sm"
                          : "border-border-subtle bg-white text-on-surface"
                      }`}
                    >
                      <CheckCircle2 className={`w-4 h-4 shrink-0 ${facilities.includes(amenity) ? "text-primary" : "text-border-subtle"}`} />
                      <span className="text-xs">{amenity}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Rules and Preferences */}
              <div className="space-y-4">
                <h3 className="text-xs font-bold text-primary uppercase tracking-wider">House Rules & Preferences</h3>
                
                <div className="flex items-center justify-between p-4 bg-white rounded-2xl border border-outline-variant/60 shadow-sm">
                  <div>
                    <p className="text-xs font-bold">Pets Allowed</p>
                    <p className="text-[10px] text-text-muted mt-0.5">Allows pets in the rented space</p>
                  </div>
                  <button 
                    type="button"
                    onClick={() => setPetsAllowed(!petsAllowed)}
                    className={`w-12 h-6 rounded-full relative transition-colors ${petsAllowed ? 'bg-primary' : 'bg-surface-container-high'}`}
                  >
                    <div className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow-sm transition-transform ${petsAllowed ? 'left-7' : 'left-1'}`} />
                  </button>
                </div>

                <div className="flex items-center justify-between p-4 bg-white rounded-2xl border border-outline-variant/60 shadow-sm">
                  <div>
                    <p className="text-xs font-bold">No Smoking</p>
                    <p className="text-[10px] text-text-muted mt-0.5">Maintains a smoke-free environment</p>
                  </div>
                  <button 
                    type="button"
                    onClick={() => setNoSmoking(!noSmoking)}
                    className={`w-12 h-6 rounded-full relative transition-colors ${noSmoking ? 'bg-primary' : 'bg-surface-container-high'}`}
                  >
                    <div className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow-sm transition-transform ${noSmoking ? 'left-7' : 'left-1'}`} />
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-[10px] font-bold text-on-surface-variant uppercase tracking-wider mb-2">Food Preference</label>
                    <select
                      value={foodPreference}
                      onChange={(e) => setFoodPreference(e.target.value)}
                      className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-2.5 text-xs font-semibold focus:outline-none"
                    >
                      <option value="Any">Veg & Non-Veg</option>
                      <option value="Veg Only">Pure Veg Only</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-on-surface-variant uppercase tracking-wider mb-2">Curfew Hours</label>
                    <select
                      value={curfew}
                      onChange={(e) => setCurfew(e.target.value)}
                      className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-2.5 text-xs font-semibold focus:outline-none"
                    >
                      <option value="No Curfew">No Curfew</option>
                      <option value="10:00 PM">10:00 PM</option>
                      <option value="11:00 PM">11:00 PM</option>
                      <option value="12:00 AM">Midnight</option>
                    </select>
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-on-surface-variant uppercase tracking-wider mb-2">Visitor Access</label>
                    <select
                      value={visitors}
                      onChange={(e) => setVisitors(e.target.value)}
                      className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-2.5 text-xs font-semibold focus:outline-none"
                    >
                      <option value="Allowed">Allowed</option>
                      <option value="Not Allowed">Not Allowed</option>
                      <option value="Only Day Visits">Only Day Visits</option>
                    </select>
                  </div>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-on-surface mb-2">Description *</label>
                <textarea
                  rows={4}
                  placeholder="Describe house rules, nearby facilities, student compatibility..."
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                  required
                />
              </div>
            </section>
          )}

          {/* Form Action Messages */}
          {error && <p className="text-xs text-error font-medium text-center">{error}</p>}
          {success && <p className="text-xs text-primary font-medium text-center">{success}</p>}

          {/* Steps Control Footer */}
          <div className="flex items-center justify-between pt-6 border-t border-outline-variant/30 mt-8 gap-4">
            <button
              type="button"
              onClick={prevStep}
              className={`px-6 py-3 rounded-xl font-bold text-xs text-primary border border-primary hover:bg-primary/5 transition-all ${
                currentStep === 1 ? "opacity-0 pointer-events-none" : ""
              }`}
            >
              Back
            </button>
            <div className="flex items-center gap-3">
              {currentStep < totalSteps ? (
                <button
                  type="button"
                  onClick={nextStep}
                  className="px-10 py-3 bg-primary text-white rounded-xl font-bold text-xs shadow-md shadow-primary/20 hover:scale-[1.02] active:scale-95 transition-all flex items-center gap-1.5"
                >
                  Continue <ChevronRight className="w-4 h-4" />
                </button>
              ) : (
                <button
                  type="submit"
                  disabled={loading}
                  className="px-10 py-3 bg-secondary-container text-white rounded-xl font-bold text-xs shadow-md shadow-secondary-container/20 hover:scale-[1.02] active:scale-95 transition-all disabled:opacity-50"
                >
                  {loading ? "Listing Property..." : "Publish Listing"}
                </button>
              )}
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
