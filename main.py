from argus.identity import Identity


def main():
    argus = Identity()

    print("=" * 60)
    print(argus.introduce())
    print("=" * 60)


if __name__ == "__main__":
    main()