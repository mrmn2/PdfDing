def parse_cron_schedule(cron_schedule: str) -> dict[str, str]:
    """
    Parse a cron schedule so that it can be used as an input for a huey periodic tasc.

    Input: '3 */2 6 7 *'
    Result: {'minute': '3', 'hour': '*/2', 'day': '6', 'month': '7', 'day_of_week': '*'}
    """

    cron_schedule_split = cron_schedule.split()
    key_list = ['minute', 'hour', 'day', 'month', 'day_of_week']
    return_dict = {key: value for key, value in zip(key_list, cron_schedule_split)}

    return return_dict
