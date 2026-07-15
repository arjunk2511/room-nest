"use client";

import { useEffect, useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { getAuthHeader } from "@/lib/supabase";
import { MapPin, Navigation, Compass, Plus, Info } from "lucide-react";

export default function PostPropertyPage() {
  const router = useRouter();
  
  // Cities/Areas dynamic dropdowns state
  const [citiesData, setCitiesData] = useState<any[]>([]);
  
  // Form Field States
  const [title, setTitle] = useState("");
  const [cityId, setCityId] = useState("");
  const [areaId, setAreaId] = useState("");
  const [price, setPrice] = useState("");
  const [deposit, setDeposit] = useState("");
  const [type, setType] = useState("1BHK");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [facilities, setFacilities] = useState("");
  const [description, setDescription] = useState("");
  const [exactLocation, setExactLocation] = useState("");
  const [latitude, setLatitude] = useState("");
  const [longitude, setLongitude] = useState("");
  
  // Image files state
  const [mainImage, setMainImage] = useState<File | null>(null);
  
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
      formData.append("facilities", facilities || "WiFi");
      formData.append("description", description);
      formData.append("exact_location", exactLocation);
      formData.append("latitude", latitude);
      formData.append("longitude", longitude);
      
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

  return (
    <div className="max-w-3xl mx-auto px-4 py-12 w-full flex-1 flex flex-col justify-center">
      <div className="bg-white border border-outline-variant rounded-2xl p-6 md:p-8 shadow-md">
        <h1 className="text-xl md:text-2xl font-extrabold font-plus-jakarta text-on-surface mb-2 text-center">Post Your Property</h1>
        <p className="text-xs text-on-surface-variant text-center mb-8">Reach thousands of premium renters in Mysore and Bangalore. Zero Brokerage.</p>

        <form onSubmit={handleFormSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-on-surface-variant mb-2">Property Title</label>
              <input
                type="text"
                placeholder="e.g. Spacious 2BHK Flat in Indiranagar"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                required
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-on-surface-variant mb-2">Stay Type</label>
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
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs font-bold text-on-surface-variant mb-2">City</label>
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
              <label className="block text-xs font-bold text-on-surface-variant mb-2">Area / Locality</label>
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
              <label className="block text-xs font-bold text-on-surface-variant mb-2">Contact Phone</label>
              <input
                type="text"
                placeholder="Owner Mobile Number"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-on-surface-variant mb-2">Rent / Month (₹)</label>
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
              <label className="block text-xs font-bold text-on-surface-variant mb-2">Security Deposit (₹)</label>
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
          <div className="border border-outline-variant rounded-2xl overflow-hidden shadow-sm">
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
                    className="px-6 py-3 bg-primary-container text-white rounded-xl text-xs font-bold inline-flex items-center gap-2 hover:opacity-90 active:scale-95 transition-all shadow-md shadow-primary/10"
                  >
                    <Navigation className="w-4 h-4" /> Detect Coordinates
                  </button>
                  {gpsStatus && <p className="text-[11px] font-medium text-on-surface-variant mt-4">{gpsStatus}</p>}
                </div>
              )}
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-on-surface-variant mb-2">Facilities / Amenities</label>
            <input
              type="text"
              placeholder="e.g. WiFi, Parking, AC, Power Backup (comma separated)"
              value={facilities}
              onChange={(e) => setFacilities(e.target.value)}
              className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-on-surface-variant mb-2">Description</label>
            <textarea
              rows={4}
              placeholder="Describe house rules, nearby facilities, student compatibility..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-surface-container-low border border-outline-variant rounded-xl p-3 text-xs focus:outline-none focus:ring-1 focus:ring-primary"
              required
            />
          </div>

          <div>
            <label className="block text-xs font-bold text-on-surface-variant mb-2">Main Property Image</label>
            <div className="border border-dashed border-outline-variant rounded-xl p-6 text-center hover:bg-surface-container-low transition-colors cursor-pointer relative">
              <input
                type="file"
                accept="image/*"
                onChange={(e) => setMainImage(e.target.files?.[0] || null)}
                className="absolute inset-0 opacity-0 cursor-pointer"
                required
              />
              <div className="flex flex-col items-center gap-2 text-text-muted">
                <Plus className="w-8 h-8 text-primary" />
                <span className="text-xs font-semibold">{mainImage ? mainImage.name : "Click or drag to upload main photo"}</span>
                <span className="text-[9px] uppercase tracking-wider">Format: WebP, PNG, JPG (Max 10MB)</span>
              </div>
            </div>
          </div>

          {error && <p className="text-xs text-error font-medium text-center">{error}</p>}
          {success && <p className="text-xs text-primary font-medium text-center">{success}</p>}

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3.5 bg-primary text-white rounded-xl text-xs font-extrabold hover:opacity-90 active:scale-95 transition-all shadow-lg shadow-primary/10 disabled:opacity-50"
          >
            {loading ? "Listing Property..." : "Submit Listing"}
          </button>
        </form>
      </div>
    </div>
  );
}
