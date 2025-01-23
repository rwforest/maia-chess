import maia_chess_backend
import argparse
import zstandard as zstd

def main():
    parser = argparse.ArgumentParser(description="Filter and process chess games based on ELO and other criteria.")
    parser.add_argument("eloMin", type=int, help="Minimum ELO rating.")
    parser.add_argument("eloMax", type=int, help="Maximum ELO rating.")
    parser.add_argument("output", help="Output file (compressed, .zst format).")
    parser.add_argument("targets", nargs="+", help="List of input game files.")
    parser.add_argument("--remove_bullet", action="store_true", help="Exclude bullet and ultrabullet games.")
    parser.add_argument("--remove_low_time", action="store_true", help="Exclude low-time moves from games.")

    args = parser.parse_args()

    games_written = 0
    print(f"Starting to write filtered games to: {args.output}")

    try:
        # Open the output file for writing in text mode with Zstandard
        with zstd.open(args.output, mode="wb") as output_file:
            for num_files, target in enumerate(sorted(args.targets)):
                print(f"Processing file {num_files + 1}/{len(args.targets)}: {target}")

                try:
                    games = maia_chess_backend.LightGamesFile(target, parseMoves=False)
                except Exception as e:
                    print(f"Error reading {target}: {e}")
                    continue

                for i, (dat, lines) in enumerate(games):
                    try:
                        # Parse ELO ratings
                        white_elo = int(dat.get("WhiteElo", 0))
                        black_elo = int(dat.get("BlackElo", 0))
                    except ValueError:
                        continue

                    # Apply filters
                    if white_elo > args.eloMax or white_elo <= args.eloMin:
                        continue
                    if black_elo > args.eloMax or black_elo <= args.eloMin:
                        continue
                    if dat.get("Result") not in ["1-0", "0-1", "1/2-1/2"]:
                        continue
                    if args.remove_bullet and "Bullet" in dat.get("Event", ""):
                        continue

                    # Write filtered games
                    if args.remove_low_time:
                        output_file.write(maia_chess_backend.remove_low_time(lines))
                    else:
                        output_file.write(lines)

                    games_written += 1

                    # Print progress every 1000 games
                    if i % 1000 == 0:
                        print(f"Processed {i} games, written {games_written} games from {target}".ljust(79), end="\r")

                print(f"Finished processing: {target}".ljust(79))

    except Exception as e:
        print(f"An error occurred while writing to {args.output}: {e}")

    print(f"Done! Total games written: {games_written}")

if __name__ == "__main__":
    main()
