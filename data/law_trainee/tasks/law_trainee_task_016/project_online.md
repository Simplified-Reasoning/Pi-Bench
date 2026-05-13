I. Feature development specification

**Document title:** Feature development specification—Nearby trending map (short-video app, international edition)  
**Target market:** United States  
**Planned launch:** Q3 2026  

**1. Feature overview**

The international short-video app adds a “Nearby trending map” entry. After the user grants permission, the system uses the device’s precise GPS location (or coarse location inferred from IP) to cluster users’ public videos on an interactive map by geography. Users can:

(1) Browse popular public videos within roughly 5 km of their location;  
(2) Tap a pin to watch a video and see the publisher’s distance and general area;  
(3) Manually select another city or region’s trending map;  
(4) When publishing, creators may choose whether to include the video on the “Nearby trending map” (default: on).

**2. Technical implementation**

The technical approach includes:

**Time-to-live (TTL) management:** Geolocation cache data uses a strict 30-day TTL; after expiry, records are physically deleted from the database.

**Third-party SDK integration**

**Map rendering:** Integrate Google Maps SDK or Mapbox. Configure the SDK to use rendering interfaces only; block the SDK from automatically collecting and uploading in-app behavioral data.

**Minor-identification engine**

**Multimodal review:** Combine voiceprint analysis, facial-feature analysis (age estimation only; no storage of biometric templates) and NLP review of comments to flag users who claim adulthood but show behavioral patterns suggestive of minors, and automatically remove them from the map pool.

**3. User experience and notice**

(1) On first entry to the “Nearby trending map” screen, show a dialog: “If you turn on precise location, your public videos may appear on nearby users’ maps, and others may see your approximate distance and neighborhood. We will not store your precise location for more than 30 days.” Offer buttons: “Allow once,” “Allow while using,” and “Deny.”  
(2) In the publishing flow, below “Who can view,” add a toggle “Allow on nearby trending map,” default on, with copy: “If on, people nearby may discover your video through the map; your nickname and approximate distance may be shown.”  
(3) Map pins show only video thumbnail, publisher nickname, and distance (e.g., “within 200 m”); they do not show specific street numbers or real-time movement trails.

**4. Special rules for minors**

(1) For registered users under 18 (United States):  
They cannot enable “Nearby trending map” browsing; none of their published videos are included in the trending map cluster; the backend periodically rescans existing content, and if AI models flag content suggestive of minors, human review follows and the item is removed from the map.

**5. Content safety and moderation**

(1) Every video shown on the map must pass machine plus human review (U.S.-based moderation team); violence, pornography, hate speech, or copyright-protected music or clips are prohibited.  
(2) Users may tap “Report” on a map pin.

**6. Data retention and deletion**

Users may delete their account or videos at any time, or turn off this feature.  
Users may “Clear historical location data” in privacy settings to immediately delete all computed caches from the past 180 days.
