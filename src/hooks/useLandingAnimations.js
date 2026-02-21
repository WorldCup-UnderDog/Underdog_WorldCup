import { useEffect } from 'react'

function useLandingAnimations(pageRef) {
  useEffect(() => {
    if (!pageRef.current) return undefined

    const root = pageRef.current
    const fills = root.querySelectorAll('.prob-bar-fill')
    const widths = ['42%', '27%', '31%']

    fills.forEach((el, i) => {
      el.style.width = '0'
      setTimeout(() => {
        el.style.width = widths[i]
      }, 900 + i * 100)
    })

    const chartObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.querySelectorAll('.chart-fill').forEach((el, i) => {
              const target = el.style.width
              el.style.width = '0'
              setTimeout(() => {
                el.style.width = target
              }, 100 + i * 80)
            })
            chartObserver.unobserve(entry.target)
          }
        })
      },
      { threshold: 0.3 }
    )

    root.querySelectorAll('.chart-card').forEach((el) => chartObserver.observe(el))

    const revealObserver = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.style.opacity = '1'
            entry.target.style.transform = 'translateY(0)'
          }
        })
      },
      { threshold: 0.1 }
    )

    root
      .querySelectorAll('.feature-card, .step-card, .bracket-card, .chart-card')
      .forEach((el) => {
        el.style.opacity = '0'
        el.style.transform = 'translateY(20px)'
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease'
        revealObserver.observe(el)
      })

    return () => {
      chartObserver.disconnect()
      revealObserver.disconnect()
    }
  }, [pageRef])
}

export default useLandingAnimations
