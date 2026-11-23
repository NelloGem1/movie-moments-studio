"""Driver: process all remaining years 2025 -> 2009 automatically."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from movie_pipeline import process_movie

YEARS = {
    2025: ["Ne Zha 2", "Zootopia 2", "Avatar Fire and Ash", "Lilo and Stitch",
           "A Minecraft Movie", "Jurassic World Rebirth", "Superman 2025",
           "Sinners", "Wicked For Good", "How to Train Your Dragon 2025"],
    2024: ["Deadpool and Wolverine", "Inside Out 2", "Dune Part Two",
           "Kingdom of the Planet of the Apes", "Alien Romulus", "Twisters",
           "Wicked", "The Wild Robot", "Furiosa", "Paddington in Peru"],
    2023: ["Barbie", "Oppenheimer", "Spider-Man Across the Spider-Verse",
           "The Super Mario Bros Movie", "John Wick Chapter 4",
           "Guardians of the Galaxy Vol 3", "Poor Things", "Mission Impossible Dead Reckoning",
           "Elemental", "Wish"],
    2022: ["Top Gun Maverick", "Avatar The Way of Water", "Doctor Strange Multiverse of Madness",
           "Elvis", "Everything Everywhere All at Once", "The Batman",
           "Jurassic World Dominion", "Black Panther Wakanda Forever",
           "Lightyear", "Minions Rise of Gru"],
    2021: ["Spider-Man No Way Home", "Dune 2021", "Encanto", "The Suicide Squad",
           "Shang-Chi", "Free Guy", "F9", "No Time to Die", "Venom Let There Be Carnage",
           "Snake Eyes"],
    2020: ["Tenet", "Soul", "Spider-Man Far From Home", "Wonder Woman 1984",
           "Trolls World Tour", "The Croods A New Age", "Mulan 2020",
           "The Trial of the Chicago 7", "The Personal History of David Copperfield",
           "Bill and Ted Face the Music"],
    2019: ["Avengers Endgame", "The Lion King 2019", "Joker", "Parasite",
           "Star Wars The Rise of Skywalker", "Toy Story 4", "Knives Out",
           "Once Upon a Time in Hollywood", "Frozen II", "Little Women"],
    2018: ["Black Panther", "Avengers Infinity War", "Deadpool 2",
           "A Star Is Born 2018", "Bohemian Rhapsody", "A Quiet Place",
           "Mission Impossible Fallout", "Spider-Man Into the Spider-Verse",
           "Incredibles 2", "Solo A Star Wars Story"],
    2017: ["Star Wars The Last Jedi", "Wonder Woman", "Get Out",
           "Thor Ragnarok", "Blade Runner 2049", "Coco", "Dunkirk",
           "Logan", "Beauty and the Beast 2017", "The Shape of Water"],
    2016: ["Rogue One", "Deadpool", "Moana", "The Jungle Book 2016",
           "La La Land", "Arrival", "Fantastic Beasts", "Captain America Civil War",
           "Finding Dory", "Suicide Squad"],
    2015: ["Star Wars The Force Awakens", "Jurassic World", "Mad Max Fury Road",
           "The Martian", "Inside Out", "Spectre", "The Revenant", "Spotlight",
           "Ant-Man", "Big Hero 6"],
    2014: ["Guardians of the Galaxy", "X-Men Days of Future Past",
           "Dawn of the Planet of the Apes", "Captain America Winter Soldier",
           "Gone Girl", "The Lego Movie", "Big Hero 6 2014", "Interstellar",
           "22 Jump Street", "Edge of Tomorrow"],
    2013: ["Gravity", "Iron Man 3", "Fast and Furious 6", "Despicable Me 2",
           "The Great Gatsby", "Her", "Frozen", "12 Years a Slave",
           "Thor The Dark World", "Man of Steel"],
    2012: ["The Avengers 2012", "The Dark Knight Rises", "Skyfall", "The Hobbit",
           "Argo", "Zero Dark Thirty", "Life of Pi", "Les Miserables",
           "The Hunger Games", "Prometheus"],
    2011: ["Harry Potter Deathly Hallows Part 2", "Transformers Dark of the Moon",
           "Rise of the Planet of the Apes", "The Help", "Midnight in Paris",
           "Drive", "Super 8", "Thor", "Fast and Furious 5", "Mission Impossible Ghost Protocol"],
    2010: ["Inception", "Toy Story 3", "The Social Network", "Iron Man 2",
           "Shutter Island", "How to Train Your Dragon", "The Kings Speech",
           "Black Swan", "Despicable Me", "Tangled"],
    2009: ["Avatar", "Up", "2012", "Star Trek", "Sherlock Holmes",
           "District 9", "Inglourious Basterds", "The Hangover",
           "Fast and Furious", "The Proposal"],
}

if __name__ == "__main__":
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 2025
    for year in sorted([y for y in YEARS if y <= start], reverse=True):
        print(f"\n########## YEAR {year} ##########", flush=True)
        for mv in YEARS[year]:
            try:
                process_movie(mv, str(year))
            except Exception as e:
                print("ERR", mv, e, flush=True)
            time.sleep(2)
        print(f"########## {year} DONE ##########\n", flush=True)
