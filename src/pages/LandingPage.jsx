import { useRef } from 'react'
import LandingNav from '../components/landing/LandingNav'
import HeroSection from '../components/landing/HeroSection'
import StatsBar from '../components/landing/StatsBar'
import FeaturesSection from '../components/landing/FeaturesSection'
import HowItWorksSection from '../components/landing/HowItWorksSection'
import VisualsSection from '../components/landing/VisualsSection'
import LandingFooter from '../components/landing/LandingFooter'
import useLandingAnimations from '../hooks/useLandingAnimations'

function LandingPage() {
  const pageRef = useRef(null)

  useLandingAnimations(pageRef)

  return (
    <div ref={pageRef}>
      <LandingNav />
      <HeroSection />
      <StatsBar />
      <FeaturesSection />
      <HowItWorksSection />
      <VisualsSection />
      <LandingFooter />
    </div>
  )
}

export default LandingPage
