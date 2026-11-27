from app.services.trading import net_worth, check_squeeze

def test_net_worth_no_positions():
    assert net_worth(25000, 0, [], []) == 25000

def test_short_profit_when_price_falls():
    # short 10 @ 100 → cash 24000, collateral 1000; price→60, liability 600
    assert net_worth(24000, 1000, [], [(10, 60)]) == 24400

def test_squeeze_trigger():
    assert check_squeeze(100, 180) and not check_squeeze(100, 179.99)

# TODO: BUY/SELL/SHORT/COVER, 35% cap, 40-share cap, price floor, 423 when paused
