import click
import piman

@click.group()
def cli():
    pass

@cli.command()
def server():    
    piman.server()

@cli.command()
@click.argument('host_ips', nargs=-1, type=click.STRING)
def restart(host_ips):
    piman.restart(host_ips)

@cli.command()
@click.argument('host_ip', nargs=1, type=click.STRING)
def reinstall(host_ip):
    piman.reinstall(host_ip)

@cli.command()
@click.argument('pi_address')
@click.argument('port_on_localhost')
def remshell(pi_address, port_on_localhost):
    piman.remshell(pi_address, port_on_localhost)

@cli.command()
@click.argument('switch_ports', nargs=-1, type=click.INT)
def powercycle(switch_ports):
    piman.powercycle(switch_ports)

if __name__ == "__main__":
    cli()
