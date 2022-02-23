#!/bin/bash

# Create the .caliValues.json file, if not already existing.

if [ ! -f /home/robot/.caliValues.json ]; then
cat > /home/robot/.caliValues.json <<- EOM
{
	"1": {
		"reflect": [1, 0],
		"rgb": {
			"red": [1, 0],
			"green": [1, 0],
			"blue": [1, 0]
		}
	},

	"2": {
		"reflect": [1, 0],
		"rgb": {
			"red": [1, 0],
			"green": [1, 0],
			"blue": [1, 0]
		}
	},

	"3": {
		"reflect": [1, 0],
		"rgb": {
			"red": [1, 0],
			"green": [1, 0],
			"blue": [1, 0]
		}
	},

	"4": {
		"reflect": [1, 0],
		"rgb": {
			"red": [1, 0],
			"green": [1, 0],
			"blue": [1, 0]
		}
	}
}
EOM
fi