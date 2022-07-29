<img align="left" alt="Project logo" src="data/icons/hicolor/scalable/apps/it.mijorus.boutique.svg" />

# Boutique
A Fast and Convenient Flatpak frontend

<p align="center">
  <img width="500" src="https://user-images.githubusercontent.com/39067225/180618676-15405cd2-dde9-4b13-970c-dd30958d5c12.png">
</p>

<p align="center">
  <img width="500" src="https://user-images.githubusercontent.com/39067225/180618679-4d0fe0b6-9264-445e-8d3c-73bc09928e73.png">
</p>


A Work-in-Progress Flatpak and Appimages app manager made with GTK4.

## Testing

(please keep in mind this is alpha software)
 
 1. Clone the repo
 2. move into the cloned repo
 3. run these commands:

```sh
# build the project 
flatpak-builder build/ it.mijorus.boutique.json --user --force-clean

# run the project
flatpak-builder --run build/ it.mijorus.boutique.json boutique
```
