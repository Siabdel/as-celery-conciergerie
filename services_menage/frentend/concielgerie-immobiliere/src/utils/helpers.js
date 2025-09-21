/**
 * Fonctions utilitaires pour les calculs et formattages
 */

/**
 * Formate une date au format DD/MM/YYYY
 * @param {string|Date} date - Date à formater
 * @returns {string} - Date formatée
 */
export function formatDate(date) {
  if (!date) return ''
  const d = new Date(date)
  const day = String(d.getDate()).padStart(2, '0')
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const year = d.getFullYear()
  return `${day}/${month}/${year}`
}

/**
 * Calcule le nombre de nuits entre deux dates
 * @param {Date} startDate - Date de début
 * @param {Date} endDate - Date de fin
 * @returns {number} - Nombre de nuits
 */
export function calculateNights(startDate, endDate) {
  if (!startDate || !endDate) return 0

  const start = new Date(startDate)
  const end = new Date(endDate)

  // Convertir en millisecondes et calculer la différence
  const diffTime = Math.abs(end - start)
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24))

  return diffDays
}

/**
 * Convertit un montant en euros
 * @param {number} amount - Montant à convertir
 * @returns {string} - Montant formaté en euro
 */
export function formatCurrency(amount) {
  if (amount === null || amount === undefined) return '0,00 €'
  return new Intl.NumberFormat('fr-FR', {
    style: 'currency',
    currency: 'EUR',
  }).format(amount)
}

/**
 * Arrondi un chiffre à 2 décimales
 * @param {number} value - Valeur à arrondir
 * @returns {number} - Valeur arrondie
 */
export function roundToTwoDecimals(value) {
  return Math.round((value + Number.EPSILON) * 100) / 100
}

/**
 * Convertit les données API en format utilisable par le composant
 * @param {Array} reservations - Réservations brutes
 * @param {Array} properties - Biens
 * @param {Array} additionalExpenses - Frais supplémentaires
 * @returns {Array} - Données traitées
 */
export function transformData(reservations, properties, additionalExpenses) {
  const propertyMap = properties.reduce((acc, property) => {
    acc[property.id] = property
    return acc
  }, {})

  const expenseMap = {}
  additionalExpenses.forEach((expense) => {
    if (!expenseMap[expense.property]) {
      expenseMap[expense.property] = []
    }
    expenseMap[expense.property].push(expense)
  })

  return reservations.map((reservation) => {
    const property = propertyMap[reservation.property]
    let serviceFee = 0
    let cleaningFee = 0
    let linensFee = 0
    let additionalExpensesForPeriod = 0

    if (property) {
      // Utilisation des frais directement dans l'API
      serviceFee = parseFloat(reservation.service_fee || 0)
      cleaningFee = parseFloat(reservation.cleaning_fee || 0)
      linensFee = parseFloat(property.linens_fee || 0)
    }

    // Calcul des frais supplémentaires pour la période
    const expensesForProperty = expenseMap[reservation.property] || []
    const start = new Date(reservation.check_in)
    const end = new Date(reservation.check_out)

    expensesForProperty.forEach((expense) => {
      const expenseDate = new Date(expense.date)
      if (expenseDate >= start && expenseDate <= end) {
        additionalExpensesForPeriod += parseFloat(expense.amount)
      }
    })

    // Calcul des commissions et totaux
    const grossAmount = roundToTwoDecimals(
      serviceFee + cleaningFee + linensFee + additionalExpensesForPeriod,
    )

    // Comm. conciergerie (15%)
    const conciergeCommissionRate = 0.15
    const conciergeCommission = roundToTwoDecimals(grossAmount * conciergeCommissionRate)

    // Comm. RBNB (10%)
    const rbnbCommissionRate = 0.1
    const rbnbCommission = roundToTwoDecimals(grossAmount * rbnbCommissionRate)

    // Revenue net client
    const netRevenue = roundToTwoDecimals(grossAmount - conciergeCommission - rbnbCommission)

    return {
      reservation_id: reservation.id,
      check_in_date: reservation.check_in,
      check_out_date: reservation.check_out,
      nights: calculateNights(reservation.check_in, reservation.check_out),
      client_name: reservation.guest_name,
      service_fee: serviceFee,
      cleaning_fee: cleaningFee,
      linens_fee: linensFee,
      additional_expenses: additionalExpensesForPeriod,
      gross_amount: grossAmount,
      concierge_commission_rate: conciergeCommissionRate * 100,
      concierge_commission: conciergeCommission,
      rbnb_commission_rate: rbnbCommissionRate * 100,
      rbnb_commission: rbnbCommission,
      net_revenue: netRevenue,
      property_name: property ? property.name : 'N/A',
    }
  })
}

/**
 * Génération du PDF avec les données
 * @param {Array} data - Données à inclure dans le PDF
 * @param {Object} options - Options de génération
 * @returns {void}
 */
export async function generatePdf(data, options = {}) {
  try {
    // Dynamically import jsPDF
    const jsPDFModule = await import('jspdf')
    const jsPDF = jsPDFModule.default

    // Dynamically import autoTable
    const autoTableModule = await import('jspdf-autotable')
    const autoTable = autoTableModule.default

    const doc = new jsPDF.default('p', 'mm', 'a4')

    // Titre
    doc.setFontSize(18)
    doc.text('Activité Conciergerie Immobilière', 105, 20, { align: 'center' })

    // Période
    const periodText = `Période : ${formatDate(options.startDate)} au ${formatDate(options.endDate)}`
    doc.setFontSize(12)
    doc.text(periodText, 105, 30, { align: 'center' })

    // En-tête du tableau
    const headers = [
      'Début',
      'Fin',
      'Nb nuitées',
      'Client',
      'Frais service',
      'Frais ménage',
      'Frais linge',
      'Montant Brut',
      'Comm. Conciergerie (%)',
      'Comm. Rbnb (%)',
      'Revenu Net',
    ]

    // Données du tableau
    const tableData = data.map((item) => [
      formatDate(item.check_in_date),
      formatDate(item.check_out_date),
      item.nights.toString(),
      item.client_name,
      formatCurrency(item.service_fee),
      formatCurrency(item.cleaning_fee),
      formatCurrency(item.linens_fee),
      formatCurrency(item.gross_amount),
      `${item.concierge_commission_rate}%`,
      `${item.rbnb_commission_rate}%`,
      formatCurrency(item.net_revenue),
    ])

    // Ajouter le tableau
    autoTable(doc, {
      head: [headers],
      body: tableData,
      startY: 40,
      theme: 'striped',
      styles: {
        fontSize: 8,
        cellPadding: 2,
      },
      headStyles: {
        fillColor: [30, 60, 114],
        textColor: 255,
      },
    })

    // Ajouter les totaux (si requis)
    if (data.length > 0) {
      const totalGross = data.reduce((sum, item) => sum + item.gross_amount, 0)
      const totalNet = data.reduce((sum, item) => sum + item.net_revenue, 0)

      doc.setFontSize(10)
      doc.text(`Total Brut: ${formatCurrency(totalGross)}`, 105, doc.lastAutoTable.finalY + 10, {
        align: 'center',
      })
      doc.text(`Total Net: ${formatCurrency(totalNet)}`, 105, doc.lastAutoTable.finalY + 15, {
        align: 'center',
      })
    }

    doc.save('activite_conciergerie.pdf')
  } catch (error) {
    console.error('Erreur lors de la génération du PDF:', error)
    alert('Erreur lors de la génération du PDF.')
  }
}

/**
 * Gestionnaire d'export iCalendar
 * @param {Array} reservations - Liste des réservations à exporter
 * @param {Function} callbackSuccess - Callback en cas de succès
 * @param {Function} callbackError - Callback en cas d'erreur
 * @returns {void}
 */
export async function exportToICal(reservations, callbackSuccess, callbackError) {
  try {
    // Chargement dynamique de ical.js
    const ical = await import('ical.js')
    const icalendar = new ical.default.Component('VCALENDAR')
    icalendar.addProperty(new ical.default.Property('VERSION', '2.0'))
    icalendar.addProperty(new ical.default.Property('PRODID', '-//Conciergerie Immobilière//FR'))

    // Pour chaque réservation, créer un événement ICS
    reservations.forEach((reservation) => {
      const event = new ical.default.Component('VEVENT')
      event.addProperty(
        new ical.default.Property('UID', `reservation-${reservation.id}@concierge.fr`),
      )
      event.addProperty(new ical.default.Property('DTSTAMP', new Date()))

      const start = new Date(reservation.check_in)
      const end = new Date(reservation.check_out)
      end.setDate(end.getDate() + 1) // Fin le lendemain

      event.addProperty(new ical.default.Property('DTSTART', start))
      event.addProperty(new ical.default.Property('DTEND', end))

      event.addProperty(
        new ical.default.Property('SUMMARY', `Réservation - ${reservation.guest_name}`),
      )
      event.addProperty(
        new ical.default.Property(
          'DESCRIPTION',
          `Client: ${reservation.guest_name}\nBien: ${reservation.property}`,
        ),
      )

      icalendar.addSubcomponent(event)
    })

    // Création du contenu ICS
    const icsContent = icalendar.toString()

    // Création du fichier et téléchargement
    const blob = new Blob([icsContent], { type: 'text/calendar;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', 'reservations.ics')
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)

    if (callbackSuccess) callbackSuccess()
  } catch (error) {
    console.error("Erreur lors de l'export iCalendar:", error)
    if (callbackError) callbackError(error)
  }
}
