# Boutique

![Schermata del 2022-07-22 22-12-16](https://user-images.githubusercontent.com/39067225/180618676-15405cd2-dde9-4b13-970c-dd30958d5c12.png)
![Schermata del 2022-07-22 22-12-43](https://user-images.githubusercontent.com/39067225/180618679-4d0fe0b6-9264-445e-8d3c-73bc09928e73.png)


A work-in-progress Flatpak and Appimages app manager.

Made with GTK4

## Testing

(please keep in mind this is alpha software)
 
 1. Clone the repo
 2. move into the cloned repo
 3. run these commands:

```sh
# builds the project 
flatpak-builder build/ it.mijorus.boutique.json --user --force-clean

# runs the project
flatpak-builder --run build/ it.mijorus.boutique.json boutique
```
