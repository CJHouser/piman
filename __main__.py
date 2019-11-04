import click
import piman


@click.group()
def cli():
    pass


@cli.command()
def server():    
    piman.server()


@cli.command()
@click.argument('switch_port', nargs=1, type=click.INT)
def restart(switch_port):
    piman.restart(switch_port)


@cli.command()
@click.argument('ip')
def reinstall(ip):
    piman.reinstall(ip)


if __name__ == "__main__":
    cli()
