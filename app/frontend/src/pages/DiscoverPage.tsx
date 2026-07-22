import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FaSearch, FaFilter, FaSlidersH } from "react-icons/fa";
import { HiSparkles } from "react-icons/hi2";
import { api } from "@/lib/api";
import type { Profile } from "@/lib/types";
import { ProfileCard } from "@/components/ProfileCard";

const interestFilters = ["All", "Tech", "Art", "Music", "Science", "Sports", "Nature"];
const typeFilters = ["All", "Human", "AI"];

const filterMap: Record<string, string[]> = {
  Tech: ["AI Research", "Quantum Physics", "Cybersecurity", "Game Dev", "UI Design", "Biotechnology", "Clean Energy"],
  Art: ["Digital Art", "Street Art", "Animation", "Photography"],
  Music: ["Synthwave", "Electronic Music", "Live Music", "Vinyl Records", "Piano", "Guitar", "Jazz"],
  Science: ["Quantum Physics", "Astronomy", "Biotechnology", "Aerospace", "AI Research"],
  Sports: ["Surfing", "Rock Climbing", "Martial Arts", "Skateboarding", "Trail Running", "Yoga", "Hiking"],
  Nature: ["Urban Farming", "Stargazing", "Hiking", "Astronomy"],
};

export default function DiscoverPage() {
  const [profiles, setProfiles] = useState<Profile[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [activeFilter, setActiveFilter] = useState("All");
  const [typeFilter, setTypeFilter] = useState("All");
  const [sortBy, setSortBy] = useState<"compatibility" | "newest">("compatibility");

  useEffect(() => {
    async function fetchProfiles() {
      const data = await api.getProfiles();
      setProfiles(data as Profile[]);
      setLoading(false);
    }
    fetchProfiles();
  }, []);

  const filtered = profiles
    .filter((p) => {
      const matchesSearch =
        !searchQuery ||
        p.display_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.location.toLowerCase().includes(searchQuery.toLowerCase()) ||
        p.interests.some((i) => i.toLowerCase().includes(searchQuery.toLowerCase()));

      const matchesType =
        typeFilter === "All" ||
        (typeFilter === "Human" && p.type === "human") ||
        (typeFilter === "AI" && p.type === "ai");

      if (activeFilter === "All") return matchesSearch && matchesType;

      const tags = filterMap[activeFilter] || [];
      return matchesSearch && matchesType && p.interests.some((i) => tags.includes(i));
    })
    .sort((a, b) => (sortBy === "compatibility" ? b.compatibility_score - a.compatibility_score : 0));

  return (
    <div className="min-h-screen pt-4 pb-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="mb-10"
        >
          <h1 className="text-3xl sm:text-4xl font-bold text-white mb-2">
            DISCOVER <span className="text-[#00ffff] neon-glow-cyan">CONNECTIONS</span>
          </h1>
          <p className="text-gray-400 font-body">Browse profiles matched to your neural frequency</p>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2, duration: 0.5 }}
          className="mb-8 space-y-4"
        >
          <div className="flex flex-col sm:flex-row gap-4">
            <div className="relative flex-1">
              <FaSearch className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-500 text-sm" />
              <input
                type="text"
                placeholder="Search by name, location, or interest..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-11 pr-4 py-3 bg-[#0a0b1a]/80 border border-[#00ffff]/15 rounded-xl text-white text-sm font-body placeholder:text-gray-600 focus:outline-none focus:border-[#00ffff]/40 transition-colors"
              />
            </div>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setSortBy(sortBy === "compatibility" ? "newest" : "compatibility")}
                className="flex items-center gap-2 px-4 py-3 glass-panel rounded-xl hover:border-[#00ffff]/30 transition-all text-sm font-body text-gray-400"
              >
                <FaSlidersH className="text-[#00ffff] text-xs" />
                {sortBy === "compatibility" ? "Top Matches" : "Newest"}
              </button>
            </div>
          </div>

          <div className="space-y-3">
            <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
              <span className="text-xs text-gray-600 font-bold tracking-wider flex-shrink-0 font-body">TYPE:</span>
              {typeFilters.map((filter) => (
                <button
                  key={filter}
                  onClick={() => setTypeFilter(filter)}
                  className={`px-4 py-1.5 rounded-full text-xs font-medium tracking-wider transition-all duration-300 whitespace-nowrap font-body ${
                    typeFilter === filter
                      ? "bg-[#ff0080]/15 text-[#ff0080] border border-[#ff0080]/40"
                      : "bg-transparent text-gray-500 border border-gray-800 hover:border-gray-600 hover:text-gray-400"
                  }`}
                >
                  {filter === "Human" ? "HUMAN" : filter === "AI" ? "AI" : "ALL"}
                </button>
              ))}
            </div>

            <div className="flex items-center gap-2 overflow-x-auto pb-2 scrollbar-none">
              <FaFilter className="text-gray-600 text-xs flex-shrink-0" />
              {interestFilters.map((filter) => (
                <button
                  key={filter}
                  onClick={() => setActiveFilter(filter)}
                  className={`px-4 py-1.5 rounded-full text-xs font-medium tracking-wider transition-all duration-300 whitespace-nowrap font-body ${
                    activeFilter === filter
                      ? "bg-[#00ffff]/15 text-[#00ffff] border border-[#00ffff]/40"
                      : "bg-transparent text-gray-500 border border-gray-800 hover:border-gray-600 hover:text-gray-400"
                  }`}
                >
                  {filter.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </motion.div>

        <div className="flex items-center gap-2 mb-6">
          <HiSparkles className="text-[#00ffff] text-sm" />
          <span className="text-sm text-gray-500 font-body">
            {loading ? "Loading..." : `${filtered.length} profile${filtered.length !== 1 ? "s" : ""} found`}
          </span>
        </div>

        {loading ? (
          <div className="flex justify-center py-20">
            <div className="w-8 h-8 border-2 border-[#00ffff]/30 border-t-[#00ffff] rounded-full animate-spin" />
          </div>
        ) : (
          <AnimatePresence mode="wait">
            <motion.div
              key={activeFilter + typeFilter + sortBy + searchQuery}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.3 }}
              className="grid sm:grid-cols-2 lg:grid-cols-3 gap-6"
            >
              {filtered.map((profile, i) => (
                <motion.div
                  key={profile.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.08, duration: 0.4 }}
                >
                  <ProfileCard profile={profile} />
                </motion.div>
              ))}
            </motion.div>
          </AnimatePresence>
        )}

        {!loading && filtered.length === 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-center py-20"
          >
            <div className="text-6xl mb-4 opacity-30">~</div>
            <h3 className="text-xl font-bold text-gray-500 mb-2">No signals detected</h3>
            <p className="text-gray-600 font-body text-sm">Try adjusting your search or filters</p>
          </motion.div>
        )}
      </div>
    </div>
  );
}
