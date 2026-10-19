# Tablet Weaving Pattern Editor

A tablet weaving pattern editor written entirely in javascript, html, css, svg. Find a running demo [here](https://snaut.github.io/tabletweaving/).

## Usage

For now I'll assume you know how to warp tablet weaving tablets and how to read tablet waving patterns. I'll update this readme with more detailed instructions and explanantions.

1. Choose number of tablets, number of holes per tablet and the number of rows in the pattern
2. Edit the warping in the lower chart. Clicking each cell cycles through colors or an empty hole. Clicking the S and Z below each columns toggles between S and Z warping of the tablet. You can add and remove colors at any time.
3. Edit the pattern in the upper chart. Clicking each cell changes the direction the tablet is turned in the step. You can always add rows to the pattern. You can change the colors to indicate forward or backward turns.
4. Download the pattern as JSON file via the "save" button.

Changing the number of tablets or holes per tablet or removing rows in the pattern is not possible without resetting the pattern.

## Planned Features

This is a hobby project, so I'll work on it whenever I feel like it.

* toggle forward / backward for whole rows
* twist counter to help with creating twist neutral patterns
* row numbers
* ~~saving~~ and loading patterns
* exporting patterns as svg
* refractor code so it's more readable
* fancier UI
* more explanantions in the tablet generator
* keyboard input
