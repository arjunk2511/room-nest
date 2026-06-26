# RoomNest Laptop Redesign & Location Feature Guideline

This document provides the design specifications, layout guidelines, and feature requirements for the desktop version of the RoomNest real estate platform. It serves as a practical implementation checklist for developers and designers.

---

## 1. Navigation Header & Spacing (Laptop / Desktop)

To improve desktop usability and visual balance, the main navigation header has been compacted. The header height is reduced, and elements are scaled down to match the proportions of premium real estate sites.

### Actionable Developer Checklist:
- **Header Height**: Reduce the main header container height from `72px` to `64px` to minimize vertical screen usage on smaller laptop displays.
- **Brand Logo**: Scale down the logo image height to `30px` and reduce the font size of the brand name to `1.35rem`.
- **Navigation Links**: Decrease the text font size of the main nav links to `0.85rem` and apply tighter horizontal padding (`6px 10px`) to prevent spacing gaps.
- **Center Search Input**: Widen the header search bar container to a maximum width of `440px` to make search interactions prominent. Use a compact input padding of `9px 14px 9px 38px` and a font size of `0.86rem`.
- **User Avatar**: Scale down the profile avatar initial circle to `32px × 32px` for a balanced look.
- **Call-To-Action Button**: Scale the "Post Property" button to `0.82rem` font size with `7px 14px` padding.

### Design Specification Table:

| UI Element | Old Style (Oversized) | New Desktop Style (Balanced) | CSS Target |
| :--- | :--- | :--- | :--- |
| Header Height | `72px` | `64px` | `.main-header` |
| Brand Logo Image | `36px` height | `30px` height | `.header-logo img` |
| Brand Text Size | `1.55rem` | `1.35rem` | `.header-logo` |
| Search Bar Width | `380px` max | `440px` max | `.header-search-wrapper` |
| Nav Link Font Size | `0.9rem` | `0.85rem` | `.nav-link-item` |
| Profile Avatar | `36px × 36px` | `32px × 32px` | `.avatar-initial` |

---

## 2. Property Cards & Image Balancing (NoBroker & Housing.com Style)

Property card images on desktop screens are resized to prevent them from taking up too much vertical space. Shorter aspect ratios are used to show more property information above the fold.

### Actionable Developer Checklist:
- **Homepage Card Images**: Change the aspect ratio of `.card-img-wrapper` on screens `≥1024px` from `16/9` (which is too tall on large monitors) to a more balanced `3/2`.
- **Search Page Card Images**: Match the homepage by changing the search card image container (`.hc-img-wrapper`) to a `3/2` aspect ratio.
- **Content Padding**: Reduce the internal padding of property cards to `1.15rem` on desktop to create a compact layout.
- **Typography Scale**: Scale down card prices on desktop to `1.25rem` (homepage) and `1.2rem` (search page), and set property titles to `0.95rem` to prevent text wrapping.

---

## 3. Page Grids & Structural Spacing (Laptop / Desktop)

Page grids are adjusted to fit properly on laptop screens and prevent misalignment on wide monitors.

### Actionable Developer Checklist:
- **Hero Section**: Reduce the main hero banner height to `420px` (minimum height `380px`) and lower the top padding to `4rem` to bring property listings higher up the page.
- **Homepage Grid Limit**: Cap the main property grid at **3 columns** instead of 4 on ultra-wide screens (`≥1440px`) to maintain a clean layout.
- **Search Page Grid**: Redesign the search results layout to use a **2-column card grid** alongside a filter sidebar. This avoids oversized single-column cards or squished three-column cards.
- **Filter Sidebar**: Set the desktop filter sidebar width to `260px` to maximize the space available for property cards.
- **Gallery Limits**: Set a maximum height of `420px` for the main image gallery on the property details page to prevent images from pushing the details section off the screen.

---

## 4. Dual-Mode Map & Location Feature (Mobile & Laptop)

A location selector is implemented on the property entry page. It prioritizes manual address entry while offering an easy transition to GPS coordinates.

### Actionable Developer Checklist:
- **Dual-Tab UI**: Place a tabbed selector above the location inputs:
  - **Tab 1 (Default)**: "Enter Address" (shows a textarea for manual entry or pasting).
  - **Tab 2**: "Use Live Location" (shows the GPS detection interface).
- **Manual Address Entry**: Ensure the address textarea is the default view so users can paste addresses immediately without browser prompts.
- **Live Geolocation**: Use the browser's `navigator.geolocation` API to retrieve coordinates when the user clicks the detection button.
- **Auto-Fill & Transition**: Upon successful GPS detection:
  - Format the latitude and longitude coordinates into the address field.
  - Generate a Google Maps link (e.g., `https://www.google.com/maps?q=lat,lng`) and insert it into the hidden/secondary `exact_location` field.
  - Automatically switch the UI tab back to "Enter Address" and focus on the textarea, allowing the user to add details like house or apartment numbers.
- **Error Handling & Fallback**: If the GPS request is denied, times out, or is unsupported, display an error message and a clear link to return to manual entry.
- **Responsive Support**: Ensure the location tabs and buttons are touch-friendly on mobile and fit within standard form containers on desktop.

---

## 5. Mobile Layout Preservation (No-Touch Zone)

To keep the mobile experience intact, all styling adjustments are isolated using CSS media queries.

### Actionable Developer Checklist:
- **CSS Media Queries**: Wrap all desktop redesign CSS rules inside `@media (min-width: 1024px)` or `@media (min-width: 1440px)` blocks.
- **Mobile Bottom Nav**: Do not alter the styles for `.bottom-nav` or `.bottom-nav-icon`. The mobile bottom nav icons must remain at `20px` with a `60px` bar height.
- **Mobile Property Cards**: Keep mobile card images at their original single-column layout with a `4/3` aspect ratio.
- **Mobile Search Overlay**: Leave the mobile search drawer and header hamburger controls untouched.

---

# Codebase Implementation Reference

The above guidelines have been applied directly to the codebase. The implementation files and line ranges are documented below:

1. **Desktop Styling Overrides**:
   - [style.css:L1869-L2150](file:///Users/nishchayramakrishna/room-nest/room-nest/static/css/style.css#L1869-L2150): Compacted header, smaller brand logo, wider search input, and resized navigation links.
   - [style.css:L2858-L2936](file:///Users/nishchayramakrishna/room-nest/room-nest/static/css/style.css#L2858-L2936): Handles `3/2` card image aspect ratios, the 2-column search grid, the compacted filter sidebar, and details page gallery constraints.
   - [search.html:L30](file:///Users/nishchayramakrishna/room-nest/room-nest/templates/search.html#L30): Sticky filter header offset set to `64px` to match the new header height.

2. **Dual-Mode Map & Geolocation**:
   - [add_property.html:L318-L375](file:///Users/nishchayramakrishna/room-nest/room-nest/templates/add_property.html#L318-L375): HTML structure for the manual address textarea, live location detection tab, and exact location inputs.
   - [add_property.html:L686-L780](file:///Users/nishchayramakrishna/room-nest/room-nest/templates/add_property.html#L686-L780): JavaScript logic for tab switching, browser-native geolocation detection, auto-filling coordinates, and error handling.
