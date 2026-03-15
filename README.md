# Easy-RPG-Maker
This is an easy way to make rpg games from a parser and a custom file structure.
All this is is a parser that is able to run .RPG files. Included within this repository is a .RPG that you can use with the provided .exe or the provided .py

here is the exact .rpg
RPG
	rooms
		room1
			description "You are in a dark cave."
			exits
				north room2
			items
				rustysword
		room2
			description "You move to a darker part of the cave and inside is another goblin."
			exits
				south room1
				west room3
				room3
			description "After that encounter you advance deeper into a small little homelike space."
			exits
				east room2
			items
				rustychestplate
	enemies
		Goblin
			hp 30
			armor 5
			atk 5
			desc "A nasty little goblin."
		Skeleton
			hp 30
			armor 0
			atk 10
			desc "a boney boi."
	items
		rustysword
			description "A rusty sword."
			actualeffect atk+5
		rustychestplate
			description "A rusty piece of armor."
			actualeffect armor+3
	start room1

# This has no relations to any other projects.
