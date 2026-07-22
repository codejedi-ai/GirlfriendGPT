import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FaCamera, FaSave, FaTimes, FaPlus, FaCheck, FaImage, FaStar, FaRegStar, FaTrash } from "react-icons/fa";
import { HiSparkles } from "react-icons/hi2";
import { api } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { ImageSlideshow } from "@/components/ImageSlideshow";

type ImageEntry = { id: number; url: string; active?: boolean };

const LOOKING_FOR_OPTIONS = [
  "Genuine Connection",
  "Long-term Relationship",
  "Something Casual",
  "Friends First",
  "Study Buddy",
  "Adventure Partner",
  "Someone Fun",
  "Creative Spark",
  "My Person",
  "Something Real",
];

const GENDER_OPTIONS = ["Male", "Female", "Non-binary", "Other", "Prefer not to say"];

const SUGGESTED_INTERESTS = [
  "Coding", "Coffee", "Hiking", "Gaming", "Music", "Photography",
  "Cooking", "Anime", "Art", "Dance", "Movies", "Reading",
  "Basketball", "Skateboarding", "Yoga", "Travel", "Ramen",
  "Board Games", "K-dramas", "Bubble Tea", "Memes", "Fashion",
  "Guitar", "Piano", "Volunteering", "Podcasts", "Stargazing",
];

interface ProfileForm {
  display_name: string;
  age: number;
  gender: string;
  bio: string;
  location: string;
  looking_for: string;
  interests: string[];
}

const EMPTY_FORM: ProfileForm = {
  display_name: "",
  age: 20,
  gender: "",
  bio: "",
  location: "",
  looking_for: "",
  interests: [],
};

export default function MyProfilePage() {
  const { user } = useAuth();
  const [form, setForm] = useState<ProfileForm>(EMPTY_FORM);
  const [profileUuid, setProfileUuid] = useState<string | null>(null);

  // Avatar state
  const [avatars, setAvatars] = useState<ImageEntry[]>([]);
  const [avatarX, setAvatarX] = useState(50);
  const [avatarY, setAvatarY] = useState(50);
  const [uploadingAvatar, setUploadingAvatar] = useState(false);
  const avatarDragRef = useRef<{ startX: number; startY: number; startAx: number; startAy: number } | null>(null);

  // Banner state
  const [banners, setBanners] = useState<ImageEntry[]>([]);
  const [bannerX, setBannerX] = useState(50);
  const [bannerY, setBannerY] = useState(50);
  const [uploadingBanner, setUploadingBanner] = useState(false);
  const bannerDragRef = useRef<{ startX: number; startY: number; startBx: number; startBy: number } | null>(null);

  // Personal images state
  const [personalImages, setPersonalImages] = useState<ImageEntry[]>([]);
  const [uploadingImage, setUploadingImage] = useState(false);

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [hasProfile, setHasProfile] = useState(false);
  const [newInterest, setNewInterest] = useState("");

  const activeAvatar = avatars.find((a) => a.active) ?? avatars[0] ?? null;
  const bannerUrls = banners.map((b) => b.url);

  useEffect(() => {
    if (!user) return;
    async function load() {
      const [data, avatarList, bannerList, imageList] = await Promise.all([
        api.getMyProfile(),
        api.getMyAvatars(),
        api.getMyBanners(),
        api.getMyPersonalImages(),
      ]);
      if (data && data.display_name !== undefined) {
        setForm({
          display_name: data.display_name || "",
          age: data.age || 20,
          gender: data.gender || "",
          bio: data.bio || "",
          location: data.location || "",
          looking_for: data.looking_for || "",
          interests: data.interests || [],
        });
        setProfileUuid(data.uuid || null);
        setAvatarX(data.avatar_x ?? 50);
        setAvatarY(data.avatar_y ?? 50);
        setBannerX(data.banner_x ?? 50);
        setBannerY(data.banner_y ?? 50);
        setHasProfile(true);
      }
      setAvatars(avatarList);
      setBanners(bannerList);
      setPersonalImages(imageList);
      setLoading(false);
    }
    load();
  }, [user]);

  const handleSave = async () => {
    if (!user) return;
    setError(null);
    if (!form.display_name.trim()) {
      setError("Display name is required");
      return;
    }
    setSaving(true);
    const payload = {
      display_name: form.display_name.trim(),
      age: form.age,
      gender: form.gender,
      bio: form.bio.trim(),
      location: form.location.trim(),
      looking_for: form.looking_for,
      interests: form.interests,
      avatar_x: avatarX,
      avatar_y: avatarY,
      banner_x: bannerX,
      banner_y: bannerY,
    };
    const result = await api.saveMyProfile(payload);
    setSaving(false);
    if (result.error) {
      setError(result.error);
    } else {
      setHasProfile(true);
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    }
  };

  const toggleInterest = (interest: string) => {
    setForm((prev) => ({
      ...prev,
      interests: prev.interests.includes(interest)
        ? prev.interests.filter((i) => i !== interest)
        : prev.interests.length < 8
          ? [...prev.interests, interest]
          : prev.interests,
    }));
  };

  const addCustomInterest = () => {
    const trimmed = newInterest.trim();
    if (!trimmed || form.interests.includes(trimmed) || form.interests.length >= 8) return;
    setForm((prev) => ({ ...prev, interests: [...prev.interests, trimmed] }));
    setNewInterest("");
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center py-20">
        <div className="w-8 h-8 border-2 border-[#00ffff]/30 border-t-[#00ffff] rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="flex-1 py-8 pb-20">
      <div className="max-w-2xl mx-auto px-4 sm:px-6">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-8"
        >
          <h1 className="text-2xl sm:text-3xl font-bold text-white mb-2 font-display tracking-wider">
            MY <span className="text-[#00ffff] neon-glow-cyan">PROFILE</span>
          </h1>
          <p className="text-gray-400 font-body text-sm">
            {hasProfile ? "Update your profile details" : "Set up your profile to start connecting"}
          </p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 15 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.15, duration: 0.5 }}
          className="space-y-6"
        >
          {/* ── AVATAR ──────────────────────────────────────────────── */}
          <div className="glass-panel rounded-2xl p-6 sm:p-8 space-y-5">
            <SectionLabel text="AVATAR" />

            <div className="flex items-start gap-5">
              {/* Active avatar circle with drag */}
              <div className="flex flex-col items-center gap-2 flex-shrink-0">
                <div
                  className="relative w-20 h-20 rounded-full overflow-hidden border-2 border-[#00ffff]/30 bg-[#0a0b1a] select-none"
                  style={{ cursor: activeAvatar ? "grab" : "default" }}
                  onMouseDown={activeAvatar ? (e) => {
                    e.preventDefault();
                    avatarDragRef.current = { startX: e.clientX, startY: e.clientY, startAx: avatarX, startAy: avatarY };
                    const onMove = (mv: MouseEvent) => {
                      if (!avatarDragRef.current) return;
                      const dx = (mv.clientX - avatarDragRef.current.startX) / 2;
                      const dy = (mv.clientY - avatarDragRef.current.startY) / 2;
                      setAvatarX(Math.min(100, Math.max(0, avatarDragRef.current.startAx - dx)));
                      setAvatarY(Math.min(100, Math.max(0, avatarDragRef.current.startAy - dy)));
                    };
                    const onUp = () => {
                      avatarDragRef.current = null;
                      window.removeEventListener("mousemove", onMove);
                      window.removeEventListener("mouseup", onUp);
                    };
                    window.addEventListener("mousemove", onMove);
                    window.addEventListener("mouseup", onUp);
                  } : undefined}
                >
                  {activeAvatar ? (
                    <img
                      src={activeAvatar.url}
                      alt="Avatar"
                      className="w-full h-full object-cover pointer-events-none"
                      style={{ objectPosition: `${avatarX}% ${avatarY}%` }}
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center">
                      <FaCamera className="text-gray-600 text-xl" />
                    </div>
                  )}
                </div>
                {activeAvatar && (
                  <p className="text-[10px] text-gray-600 font-body">drag to reposition</p>
                )}
              </div>

              <div className="flex-1">
                <label className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg bg-[#0a0b1a]/80 border border-[#00ffff]/15 text-[#00ffff] text-sm font-body cursor-pointer hover:border-[#00ffff]/40 transition-all">
                  <FaCamera className="text-xs" />
                  {uploadingAvatar ? "UPLOADING..." : avatars.length ? "ADD AVATAR PHOTO" : "UPLOAD AVATAR"}
                  <input
                    type="file"
                    accept="image/*"
                    className="hidden"
                    disabled={uploadingAvatar}
                    onChange={async (e) => {
                      const file = e.target.files?.[0];
                      if (!file) return;
                      setUploadingAvatar(true);
                      const result = await api.uploadAvatar(file);
                      setUploadingAvatar(false);
                      if (result.data) {
                        setAvatars(result.data);
                        setAvatarX(50);
                        setAvatarY(50);
                      } else {
                        setError(result.error ?? "Upload failed");
                      }
                    }}
                  />
                </label>
                <p className="text-[11px] text-gray-600 mt-1.5 font-body">
                  UUID: <code className="text-gray-500 break-all">{profileUuid ?? '...'}</code>
                </p>
              </div>
            </div>

            {/* Avatar image grid */}
            {avatars.length > 0 && (
              <ImageGrid
                images={avatars}
                onActivate={async (id) => {
                  const updated = await api.activateAvatar(id);
                  if (updated) setAvatars(updated);
                }}
                onDelete={async (id) => {
                  const updated = await api.deleteAvatar(id);
                  if (updated) setAvatars(updated);
                }}
                showActivate
              />
            )}
          </div>

          {/* ── BANNER ──────────────────────────────────────────────── */}
          <div className="glass-panel rounded-2xl p-6 sm:p-8 space-y-5">
            <SectionLabel text="BANNER" />

            {/* Banner slideshow preview */}
            <div
              className="relative w-full h-36 rounded-xl overflow-hidden border border-[#00ffff]/15 bg-[#0a0b1a] select-none"
              style={{ cursor: bannerUrls.length ? "grab" : "default" }}
              onMouseDown={bannerUrls.length ? (e) => {
                e.preventDefault();
                bannerDragRef.current = { startX: e.clientX, startY: e.clientY, startBx: bannerX, startBy: bannerY };
                const onMove = (mv: MouseEvent) => {
                  if (!bannerDragRef.current) return;
                  const dx = (mv.clientX - bannerDragRef.current.startX) / 3;
                  const dy = (mv.clientY - bannerDragRef.current.startY) / 3;
                  setBannerX(Math.min(100, Math.max(0, bannerDragRef.current.startBx - dx)));
                  setBannerY(Math.min(100, Math.max(0, bannerDragRef.current.startBy - dy)));
                };
                const onUp = () => {
                  bannerDragRef.current = null;
                  window.removeEventListener("mousemove", onMove);
                  window.removeEventListener("mouseup", onUp);
                };
                window.addEventListener("mousemove", onMove);
                window.addEventListener("mouseup", onUp);
              } : undefined}
            >
              {bannerUrls.length ? (
                <ImageSlideshow
                  urls={bannerUrls}
                  objectX={bannerX}
                  objectY={bannerY}
                  alt="Banner"
                  className="w-full h-full object-cover pointer-events-none"
                  interval={5000}
                />
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <FaImage className="text-gray-700 text-2xl" />
                </div>
              )}
              {bannerUrls.length > 1 && (
                <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded-full bg-black/60 text-[10px] text-gray-400 font-body">
                  {bannerUrls.length} photos · slideshow
                </div>
              )}
            </div>
            {bannerUrls.length > 0 && (
              <p className="text-[10px] text-gray-600 font-body -mt-2">drag preview to reposition · save profile to apply</p>
            )}

            <label className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg bg-[#0a0b1a]/80 border border-[#00ffff]/15 text-[#00ffff] text-sm font-body cursor-pointer hover:border-[#00ffff]/40 transition-all">
              <FaCamera className="text-xs" />
              {uploadingBanner ? "UPLOADING..." : banners.length ? "ADD BANNER PHOTO" : "UPLOAD BANNER"}
              <input
                type="file"
                accept="image/*"
                className="hidden"
                disabled={uploadingBanner}
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  setUploadingBanner(true);
                  const result = await api.uploadBanner(file);
                  setUploadingBanner(false);
                  if (result.data) {
                    setBanners(result.data);
                    setBannerX(50);
                    setBannerY(50);
                  } else {
                    setError(result.error ?? "Upload failed");
                  }
                }}
              />
            </label>

            {/* Banner image grid */}
            {banners.length > 0 && (
              <ImageGrid
                images={banners}
                onActivate={async (id) => {
                  const updated = await api.activateBanner(id);
                  if (updated) setBanners(updated);
                }}
                onDelete={async (id) => {
                  const updated = await api.deleteBanner(id);
                  if (updated) setBanners(updated);
                }}
                showActivate
              />
            )}
          </div>

          {/* ── MY PHOTOS ───────────────────────────────────────────── */}
          <div className="glass-panel rounded-2xl p-6 sm:p-8 space-y-5">
            <SectionLabel text="MY PHOTOS" />
            <p className="text-[11px] text-gray-500 font-body -mt-2">Personal photos stored in your gallery</p>

            <label className="flex items-center justify-center gap-2 w-full px-4 py-2.5 rounded-lg bg-[#0a0b1a]/80 border border-[#ff0080]/15 text-[#ff0080] text-sm font-body cursor-pointer hover:border-[#ff0080]/40 transition-all">
              <FaPlus className="text-xs" />
              {uploadingImage ? "UPLOADING..." : "ADD PHOTO"}
              <input
                type="file"
                accept="image/*"
                className="hidden"
                disabled={uploadingImage}
                onChange={async (e) => {
                  const file = e.target.files?.[0];
                  if (!file) return;
                  setUploadingImage(true);
                  const result = await api.uploadPersonalImage(file);
                  setUploadingImage(false);
                  if (result.data) {
                    setPersonalImages((prev) => [result.data!, ...prev]);
                  } else {
                    setError(result.error ?? "Upload failed");
                  }
                }}
              />
            </label>

            {personalImages.length > 0 ? (
              <ImageGrid
                images={personalImages}
                onDelete={async (id) => {
                  const ok = await api.deletePersonalImage(id);
                  if (ok) setPersonalImages((prev) => prev.filter((i) => i.id !== id));
                }}
                showActivate={false}
              />
            ) : (
              <div className="text-center py-6 text-gray-600 font-body text-sm">
                No photos yet
              </div>
            )}
          </div>

          {/* ── PROFILE INFO ────────────────────────────────────────── */}
          <div className="glass-panel rounded-2xl p-6 sm:p-8 space-y-6">
            <SectionLabel text="BASIC INFO" />
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <FieldGroup label="DISPLAY NAME">
                <input
                  type="text"
                  maxLength={30}
                  placeholder="Your name"
                  value={form.display_name}
                  onChange={(e) => setForm((p) => ({ ...p, display_name: e.target.value }))}
                  className="w-full px-4 py-2.5 rounded-lg bg-[#0a0b1a]/80 border border-[#00ffff]/15 text-white text-sm font-body placeholder-gray-600 focus:outline-none focus:border-[#00ffff]/40 transition-all"
                />
              </FieldGroup>

              <FieldGroup label="AGE">
                <input
                  type="number"
                  min={18}
                  max={99}
                  value={form.age}
                  onChange={(e) => setForm((p) => ({ ...p, age: Math.max(18, Math.min(99, Number(e.target.value))) }))}
                  className="w-full px-4 py-2.5 rounded-lg bg-[#0a0b1a]/80 border border-[#00ffff]/15 text-white text-sm font-body placeholder-gray-600 focus:outline-none focus:border-[#00ffff]/40 transition-all"
                />
              </FieldGroup>

              <FieldGroup label="GENDER">
                <select
                  value={form.gender}
                  onChange={(e) => setForm((p) => ({ ...p, gender: e.target.value }))}
                  className="w-full px-4 py-2.5 rounded-lg bg-[#0a0b1a]/80 border border-[#00ffff]/15 text-white text-sm font-body focus:outline-none focus:border-[#00ffff]/40 transition-all appearance-none"
                >
                  <option value="" className="bg-[#0a0b1a]">Select...</option>
                  {GENDER_OPTIONS.map((g) => (
                    <option key={g} value={g} className="bg-[#0a0b1a]">{g}</option>
                  ))}
                </select>
              </FieldGroup>

              <FieldGroup label="LOCATION">
                <input
                  type="text"
                  maxLength={50}
                  placeholder="City, Province"
                  value={form.location}
                  onChange={(e) => setForm((p) => ({ ...p, location: e.target.value }))}
                  className="w-full px-4 py-2.5 rounded-lg bg-[#0a0b1a]/80 border border-[#00ffff]/15 text-white text-sm font-body placeholder-gray-600 focus:outline-none focus:border-[#00ffff]/40 transition-all"
                />
              </FieldGroup>
            </div>

            <div className="border-t border-white/5" />

            <SectionLabel text="ABOUT YOU" />
            <FieldGroup label="BIO">
              <textarea
                maxLength={300}
                rows={4}
                placeholder="Tell people about yourself..."
                value={form.bio}
                onChange={(e) => setForm((p) => ({ ...p, bio: e.target.value }))}
                className="w-full px-4 py-3 rounded-lg bg-[#0a0b1a]/80 border border-[#00ffff]/15 text-white text-sm font-body placeholder-gray-600 focus:outline-none focus:border-[#00ffff]/40 transition-all resize-none"
              />
              <p className="text-[11px] text-gray-600 mt-1 font-body text-right">{form.bio.length}/300</p>
            </FieldGroup>

            <FieldGroup label="LOOKING FOR">
              <div className="flex flex-wrap gap-2">
                {LOOKING_FOR_OPTIONS.map((opt) => (
                  <button
                    key={opt}
                    type="button"
                    onClick={() => setForm((p) => ({ ...p, looking_for: p.looking_for === opt ? "" : opt }))}
                    className={`px-3.5 py-1.5 rounded-full text-xs font-medium tracking-wide transition-all duration-200 font-body ${
                      form.looking_for === opt
                        ? "bg-[#ff0080]/15 text-[#ff0080] border border-[#ff0080]/40"
                        : "bg-transparent text-gray-500 border border-gray-800 hover:border-gray-600 hover:text-gray-400"
                    }`}
                  >
                    {opt}
                  </button>
                ))}
              </div>
            </FieldGroup>

            <div className="border-t border-white/5" />

            <SectionLabel text="INTERESTS" />
            <p className="text-[11px] text-gray-500 font-body -mt-3">
              Pick up to 8 interests ({form.interests.length}/8)
            </p>

            {form.interests.length > 0 && (
              <div className="flex flex-wrap gap-2">
                {form.interests.map((interest) => (
                  <span
                    key={interest}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium bg-[#00ffff]/10 text-[#00ffff] border border-[#00ffff]/30 font-body"
                  >
                    {interest}
                    <button
                      type="button"
                      onClick={() => toggleInterest(interest)}
                      className="hover:text-white transition-colors"
                    >
                      <FaTimes className="text-[8px]" />
                    </button>
                  </span>
                ))}
              </div>
            )}

            <div className="flex flex-wrap gap-2">
              {SUGGESTED_INTERESTS.filter((i) => !form.interests.includes(i)).map((interest) => (
                <button
                  key={interest}
                  type="button"
                  onClick={() => toggleInterest(interest)}
                  disabled={form.interests.length >= 8}
                  className="px-3 py-1.5 rounded-full text-xs font-medium text-gray-500 border border-gray-800 hover:border-gray-600 hover:text-gray-400 transition-all duration-200 font-body disabled:opacity-30 disabled:cursor-not-allowed"
                >
                  {interest}
                </button>
              ))}
            </div>

            <div className="flex gap-2">
              <input
                type="text"
                maxLength={25}
                placeholder="Add custom interest..."
                value={newInterest}
                onChange={(e) => setNewInterest(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addCustomInterest())}
                className="flex-1 px-4 py-2 rounded-lg bg-[#0a0b1a]/80 border border-[#00ffff]/15 text-white text-sm font-body placeholder-gray-600 focus:outline-none focus:border-[#00ffff]/40 transition-all"
              />
              <button
                type="button"
                onClick={addCustomInterest}
                disabled={!newInterest.trim() || form.interests.length >= 8}
                className="px-3 py-2 rounded-lg border border-[#00ffff]/30 text-[#00ffff] hover:bg-[#00ffff]/10 transition-all disabled:opacity-30 disabled:cursor-not-allowed"
              >
                <FaPlus className="text-xs" />
              </button>
            </div>
          </div>

          <AnimatePresence>
            {error && (
              <motion.div
                initial={{ opacity: 0, y: -5 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0 }}
                className="p-3 rounded-lg border border-red-500/30 bg-red-500/10 text-red-400 text-sm font-body text-center"
              >
                {error}
              </motion.div>
            )}
          </AnimatePresence>

          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={handleSave}
            disabled={saving}
            className="w-full flex items-center justify-center gap-3 py-3.5 bg-gradient-to-r from-[#ff0080] to-[#cc0066] text-white font-bold text-xs tracking-wider rounded-xl transition-all duration-300 hover:shadow-lg hover:shadow-[#ff0080]/20 font-display disabled:opacity-50"
          >
            {saving ? (
              "SAVING..."
            ) : saved ? (
              <>
                <FaCheck className="text-[10px]" />
                SAVED
              </>
            ) : (
              <>
                <FaSave className="text-[10px]" />
                {hasProfile ? "UPDATE PROFILE" : "CREATE PROFILE"}
              </>
            )}
          </motion.button>
        </motion.div>
      </div>
    </div>
  );
}

// ── Shared image grid with activate/delete controls ────────────────────────────

interface ImageGridProps {
  images: ImageEntry[];
  onActivate?: (id: number) => void;
  onDelete: (id: number) => void;
  showActivate: boolean;
}

function ImageGrid({ images, onActivate, onDelete, showActivate }: ImageGridProps) {
  return (
    <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">
      {images.map((img) => (
        <div key={img.id} className="relative group aspect-square rounded-lg overflow-hidden border border-white/10">
          <img
            src={img.url}
            alt=""
            className="w-full h-full object-cover"
          />
          {/* Active badge */}
          {showActivate && img.active && (
            <div className="absolute top-1 left-1 w-5 h-5 rounded-full bg-[#00ffff] flex items-center justify-center">
              <FaStar className="text-black text-[8px]" />
            </div>
          )}
          {/* Hover overlay */}
          <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
            {showActivate && !img.active && onActivate && (
              <button
                title="Set as active"
                onClick={() => onActivate(img.id)}
                className="w-7 h-7 rounded-full bg-[#00ffff]/20 border border-[#00ffff]/50 flex items-center justify-center hover:bg-[#00ffff]/40 transition-colors"
              >
                <FaRegStar className="text-[#00ffff] text-[10px]" />
              </button>
            )}
            <button
              title="Delete"
              onClick={() => onDelete(img.id)}
              className="w-7 h-7 rounded-full bg-red-500/20 border border-red-500/50 flex items-center justify-center hover:bg-red-500/40 transition-colors"
            >
              <FaTrash className="text-red-400 text-[10px]" />
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}

function SectionLabel({ text }: { text: string }) {
  return (
    <div className="flex items-center gap-2">
      <HiSparkles className="text-[#00ffff] text-xs" />
      <span className="text-xs text-gray-400 tracking-widest font-display font-bold">{text}</span>
    </div>
  );
}

function FieldGroup({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <label className="block text-[10px] text-gray-500 tracking-wider font-display mb-1.5">{label}</label>
      {children}
    </div>
  );
}
