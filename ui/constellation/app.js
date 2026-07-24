const services = {
  hanuman: {
    title: 'Hanuman',
    description: "Le centre de gravité de l’écosystème. Hanuman ne remplace aucun outil : il coordonne les flux et rend visibles les liens entre eux.",
    status: '<strong>● Opérationnel</strong><br>7 intégrations répertoriées<br>1 orchestration mise en avant',
    actions: ['Voir les orchestrations', 'Consulter l’activité', 'Ouvrir la documentation']
  },
  github: {
    title: 'GitHub',
    description: 'Dépôts, issues, projets et activité de développement reliés au reste de votre environnement.',
    status: '<strong>● Connecté</strong><br>Lecture des dépôts et des issues disponible',
    actions: ['Explorer les dépôts', 'Voir les issues', 'Lancer une synchronisation']
  },
  notion: {
    title: 'Notion',
    description: 'Espace de publication et d’organisation. Les pages deviennent des destinations de flux, non des silos.',
    status: '<strong>● Connecté</strong><br>Création, mise à jour et recherche disponibles',
    actions: ['Voir les pages', 'Créer une page', 'Historique des synchronisations']
  },
  obsidian: {
    title: 'Obsidian',
    description: 'Le vault local constitue la mémoire personnelle de Hanuman et la source des notes Markdown.',
    status: '<strong>● Vault local détecté</strong><br>Chemin configuré côté serveur',
    actions: ['Explorer le vault', 'Synchroniser vers Notion', 'Voir les conflits']
  },
  calendar: {
    title: 'Calendar',
    description: 'Les événements et les échéances deviennent visibles dans les orchestrations de Hanuman.',
    status: '<strong>● Intégration déclarée</strong><br>Lecture, création et synchronisation prévues',
    actions: ['Voir les événements', 'Créer un événement', 'État de la connexion']
  },
  chess: {
    title: 'Chess.com',
    description: 'Parties, analyses et exports peuvent rejoindre Obsidian ou alimenter d’autres workflows.',
    status: '<strong>● Connecté</strong><br>Lecture, analyse et export disponibles',
    actions: ['Voir les parties', 'Analyser une partie', 'Exporter vers Obsidian']
  },
  wikipedia: {
    title: 'Wikipedia',
    description: 'Une source documentaire externe pour enrichir les recherches et générer des context packs.',
    status: '<strong>● Connecté</strong><br>Recherche et extraction disponibles',
    actions: ['Rechercher', 'Créer un context pack', 'Voir les sources récentes']
  },
  gmail: {
    title: 'Gmail',
    description: "Cette étoile est volontairement distante : Gmail n’est pas encore déclaré comme intégration active dans le dépôt.",
    status: '○ Non connecté<br>Aucune route active détectée',
    actions: ['Préparer le connecteur', 'Définir les permissions', 'Masquer cette étoile']
  },
  sync: {
    title: 'Obsidian ↔ Notion',
    description: 'Une orchestration bidirectionnelle entre le vault Markdown local et l’espace Notion.',
    status: '<strong>● Flux prioritaire</strong><br>État visuel simulé dans cette V1',
    actions: ['Synchroniser maintenant', 'Voir les conflits', 'Ouvrir l’historique']
  },
  search: {
    title: 'Recherche universelle',
    description: 'Un futur point d’entrée unique pour interroger les contenus reliés sans se soucier de leur emplacement réel.',
    status: 'Prototype d’interface<br>Backend non branché',
    actions: ['Rechercher “Ambroise Thomas”', 'Choisir les sources', 'Voir l’indexation']
  },
  activity: {
    title: 'Activité',
    description: 'La respiration du système : synchronisations, erreurs, créations et transformations.',
    status: '<strong>● 3 flux simulés</strong><br>La télémétrie réelle sera branchée ensuite',
    actions: ['Voir le journal', 'Filtrer les erreurs', 'Afficher les dernières 24 h']
  },
  settings: {
    title: 'Réglages',
    description: 'Configuration des connecteurs, permissions, préférences visuelles et règles d’orchestration.',
    status: 'Interface à construire',
    actions: ['Gérer les connecteurs', 'Préférences visuelles', 'Sécurité']
  }
};

const panel = document.querySelector('.inspector');
const backdrop = document.querySelector('.backdrop');
const title = document.querySelector('#panel-title');
const description = document.querySelector('#panel-description');
const status = document.querySelector('#panel-status');
const actions = document.querySelector('#panel-actions');

function openPanel(key) {
  const service = services[key] || services.hanuman;
  title.textContent = service.title;
  description.textContent = service.description;
  status.innerHTML = service.status;
  actions.innerHTML = service.actions.map(action => `<button type="button">${action}</button>`).join('');
  panel.classList.add('open');
  panel.setAttribute('aria-hidden', 'false');
  backdrop.hidden = false;
}

function closePanel() {
  panel.classList.remove('open');
  panel.setAttribute('aria-hidden', 'true');
  backdrop.hidden = true;
}

document.querySelectorAll('[data-service]').forEach(element => {
  element.addEventListener('click', () => openPanel(element.dataset.service));
});

document.querySelector('.close-panel').addEventListener('click', closePanel);
backdrop.addEventListener('click', closePanel);
document.addEventListener('keydown', event => {
  if (event.key === 'Escape') closePanel();
  if ((event.metaKey || event.ctrlKey) && event.key.toLowerCase() === 'k') {
    event.preventDefault();
    openPanel('search');
  }
});