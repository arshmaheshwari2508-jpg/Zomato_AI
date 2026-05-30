---
name: Luminous Gastronomy
colors:
  surface: '#fcf9f8'
  surface-dim: '#dcd9d9'
  surface-bright: '#fcf9f8'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3f2'
  surface-container: '#f0eded'
  surface-container-high: '#eae7e7'
  surface-container-highest: '#e5e2e1'
  on-surface: '#1b1b1b'
  on-surface-variant: '#5b403f'
  inverse-surface: '#313030'
  inverse-on-surface: '#f3f0ef'
  outline: '#8f6f6e'
  outline-variant: '#e4bebc'
  surface-tint: '#bb162c'
  primary: '#b7122a'
  on-primary: '#ffffff'
  primary-container: '#db313f'
  on-primary-container: '#fffbff'
  inverse-primary: '#ffb3b1'
  secondary: '#b90040'
  on-secondary: '#ffffff'
  secondary-container: '#de2656'
  on-secondary-container: '#fffbff'
  tertiary: '#b51c00'
  on-tertiary: '#ffffff'
  tertiary-container: '#dc3214'
  on-tertiary-container: '#fffbff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdad8'
  primary-fixed-dim: '#ffb3b1'
  on-primary-fixed: '#410007'
  on-primary-fixed-variant: '#92001c'
  secondary-fixed: '#ffd9dc'
  secondary-fixed-dim: '#ffb2ba'
  on-secondary-fixed: '#400011'
  on-secondary-fixed-variant: '#910031'
  tertiary-fixed: '#ffdad3'
  tertiary-fixed-dim: '#ffb4a5'
  on-tertiary-fixed: '#3e0400'
  on-tertiary-fixed-variant: '#8e1300'
  background: '#fcf9f8'
  on-background: '#1b1b1b'
  surface-variant: '#e5e2e1'
typography:
  display-lg:
    fontFamily: Outfit
    fontSize: 48px
    fontWeight: '700'
    lineHeight: 56px
    letterSpacing: -0.02em
  headline-lg:
    fontFamily: Outfit
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.01em
  headline-lg-mobile:
    fontFamily: Outfit
    fontSize: 28px
    fontWeight: '600'
    lineHeight: 36px
  headline-md:
    fontFamily: Outfit
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  body-lg:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
  body-md:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-sm:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.05em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  base: 8px
  xs: 4px
  sm: 12px
  md: 16px
  lg: 24px
  xl: 32px
  gutter: 16px
  margin-mobile: 20px
  margin-desktop: 40px
---

## Brand & Style
The design system is engineered for a premium, high-intent food discovery experience. It balances the energy of the culinary world with a sophisticated, tech-forward aesthetic. The personality is curated, appetizing, and effortless.

The visual direction utilizes **Glassmorphism** to create a sense of depth and hierarchy without clutter. By using translucent surfaces and background blurs, the UI allows high-quality food photography to remain the focal point, acting as the "environment" behind the interface. This creates an immersive experience where the product feels like a lens over the physical world of dining.

## Colors
The palette is anchored by the signature primary red, refined for a premium context. While the foundational colors are Crisp White and Deep Charcoal, the accent system uses a vibrant gradient from Sunset Orange to Ruby Red to denote "active" discovery states and premium features.

- **Primary Red:** Used for critical actions, branding, and high-priority status indicators.
- **Surface Strategy:** Use white glass (light mode) or charcoal glass (dark mode) for cards and overlays.
- **Semantic Colors:** Success (Green), Warning (Amber), and Error (Red) should maintain high saturation to be visible against blurred backgrounds.

## Typography
The typography system uses **Outfit** for expressive, modern headings that feel welcoming yet sharp. **Inter** is utilized for all functional UI elements and long-form descriptions to ensure maximum legibility at smaller sizes.

- **Headings:** Use tight letter-spacing on larger sizes to maintain a premium, editorial feel.
- **Body:** Prioritize generous line heights (1.5x) to prevent eye fatigue during menu browsing.
- **Accessibility:** Never use a font size smaller than 12px. Ensure labels have high contrast against glass backgrounds.

## Layout & Spacing
The layout follows a **fluid grid** logic with specific constraints for mobile-first food discovery. 

- **Grid:** Use a 4-column grid for mobile and a 12-column grid for desktop.
- **Rhythm:** An 8px linear scale governs all padding and margins. 
- **Safe Areas:** Implement generous bottom padding (min 32px) on mobile to ensure touch targets for filters and navigation are reachable.
- **Reflow:** On tablet and desktop, food cards transition from single-column lists to multi-column masonry grids to maximize visual density.

## Elevation & Depth
Depth is achieved through a combination of **backdrop blurs** (blur-radius: 20px to 40px) and **ambient shadows**.

- **Level 1 (Base):** Flat backgrounds or photography.
- **Level 2 (Cards):** 70% opacity white with a 1px inner border (10% opacity white) to simulate the edge of a glass pane. Soft shadow: `0 4px 12px rgba(0,0,0,0.05)`.
- **Level 3 (Modals/Overlays):** 85% opacity white. Deeper shadow: `0 12px 32px rgba(0,0,0,0.15)`.
- **Transitions:** All state changes (hover, active, modal entry) must use a 300ms ease-out timing to feel fluid and high-end.

## Shapes
The shape language is consistently **Rounded**, reflecting a modern and friendly approachable vibe.

- **Cards & Inputs:** 0.5rem (8px) base radius.
- **Large Surfaces (Modals/Banners):** 1.5rem (24px) to create a soft, organic frame for food imagery.
- **Interactive Elements:** Buttons and filter chips should utilize a 1rem (16px) radius to distinguish them as clickable objects from the content cards.

## Components
- **Buttons:** Primary buttons use the Sunset Orange to Ruby Red gradient with white text. Secondary buttons use a glass effect with a subtle 1px border. Minimum height: 48px for mobile accessibility.
- **Filter Chips:** Pill-shaped with a 1px border. Active state: Zomato Red background with white text. Inactive state: Translucent grey background.
- **Food Cards:** Full-width imagery with a glass-morphic text overlay at the bottom for the restaurant name and rating. Use a 1:1 or 4:3 aspect ratio.
- **Visual Rating System:** Use the Zomato Red for star icons. Use a weighted bar for review distributions.
- **Input Fields:** Semi-transparent background with a clear focus ring in Zomato Red. Use "Outfit" for placeholder text to match heading aesthetics.
- **Bottom Navigation:** A high-blur glass bar with haptic-ready icons. Active state is indicated by a small dot and color change to primary red.