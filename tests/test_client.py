from src.reservix_client import ReservixClient

SAMPLE_CALENDAR_HTML = """
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
<div id="calendar"></div>
<script>
    $(function() {
        rx.ReactApps.calendar({
            rootElementId: 'calendar',
            events: [
                {
                    "id": 1001,
                    "startDateTime": 1795798200000,
                    "endDateTime": 1795807200000,
                    "utcOffset": 3600,
                    "isBookable": true,
                    "name": "Weihnachtsmarkt Titisee",
                    "syncId": "2601980",
                    "urlPath": "tickets-titisee/e2601980",
                    "bookableInfo": "Ausverkauft"
                },
                {
                    "id": 1002,
                    "startDateTime": 1795798200000,
                    "endDateTime": 1795807200000,
                    "utcOffset": 3600,
                    "isBookable": false,
                    "name": "Weihnachtsmarkt Hinterzarten",
                    "syncId": "2601981",
                    "urlPath": "tickets-hinterzarten/e2601981",
                    "bookableInfo": "Ausverkauft"
                }
            ]
        });
    });
</script>
</body>
</html>
"""


def test_parse_calendar_script():
    client = ReservixClient()
    slots = client._parse_calendar_script(SAMPLE_CALENDAR_HTML, group_id=545832, group_name="Shuttle Titisee")

    assert len(slots) == 2
    s1, s2 = slots[0], slots[1]

    assert s1.id == 1001
    assert s1.sync_id == "2601980"
    assert s1.is_bookable is True
    assert s1.name == "Weihnachtsmarkt Titisee"
    assert s1.group_name == "Shuttle Titisee"

    assert s2.id == 1002
    assert s2.is_bookable is False
