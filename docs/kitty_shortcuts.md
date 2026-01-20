# Raccourcis Kitty (rappel rapide)

Pour créer un raccourci dans Kitty, il suffit d’ajouter une ligne `map` dans
`~/.config/kitty/kitty.conf`, puis de recharger la configuration.

## Exemple minimal

```conf
# Ouvre un nouvel onglet
map ctrl+shift+t new_tab

# Ouvre une nouvelle fenêtre
map ctrl+shift+enter new_window

# Recharge la configuration
map ctrl+shift+r reload_config
```

## Étapes

1. Ouvre `~/.config/kitty/kitty.conf`.
2. Ajoute tes lignes `map`.
3. Recharge Kitty (`kitty +kitten --reload-config` ou le raccourci que tu as défini).

Tu peux adapter les touches et les actions selon tes besoins.
