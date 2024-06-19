from loguru import logger

logger.add(
    "debug.json",
    format="{time} {level} {message}",
    level="WARNING",
    rotation="10 KB",
    # rotation="10:00",
    # rotation="10 day",
    compression="zip",
    serialize=True,
)



def divide(a, b):
    return a/b


@logger.catch
def main():
    divide(1,0)


main()