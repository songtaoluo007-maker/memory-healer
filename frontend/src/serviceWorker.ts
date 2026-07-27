export async function syncServiceWorker(production: boolean): Promise<void> {
  if (!('serviceWorker' in navigator)) return

  if (!production) {
    const registrations = await navigator.serviceWorker.getRegistrations()
    await Promise.all(registrations.map((registration) => registration.unregister()))
    return
  }

  await navigator.serviceWorker.register('/sw.js')
}
