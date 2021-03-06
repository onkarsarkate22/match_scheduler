import math
from django.conf import settings
from django.http import HttpResponseRedirect
from .models import LoginCredential, Match, Point, Pool
from django.shortcuts import render, HttpResponse, redirect, render_to_response
from django.core.mail import send_mail


# Basic home page(information about spofit)
def get_information(request):
    return render(request, 'home/information.html')


def schedule(request, pool_number=1):
    pool_number = int(pool_number)
    if request.is_ajax():
        print('HeLlO')
        text = request.POST.get('winner_name').split(' ')
        match_id = text[1]
        winner = text[0]
        user_id = request.session['user_id']
        user_obj = LoginCredential.objects.get(id=user_id)
        print(winner)
        print(user_id)
        if request.is_ajax:
            pool_obj = user_obj.pool_set.get(pool_number=pool_number)
            match_obj_rows = pool_obj.match_set
            match_obj = match_obj_rows.get(id=match_id)
            if match_obj.winner == '0':
                point_obj = Point.objects.get(pool=pool_obj, team=winner)
                point_obj.wins += 2
                point_obj.save()
            if match_obj.team1 == winner:
                match_obj.winner = '1'
            else:
                match_obj.winner = '2'
            match_obj.save()
            return HttpResponse("Yipeee done(AJAX)" + str(match_id) + str(winner))
        else:
            return HttpResponse("Not Ajax")
    elif request.method == 'POST':
        if request.POST.get('submit'):
            # print("submit")
            type = 0
            group1 = []
            group2 = []
            list1 = []
            list2 = []
            user_name = request.POST.get('user_name')
            password = request.POST.get('password')
            type_of_match = request.POST.get('type_of_match')
            if type_of_match == 'League matches':
                type = 1
            elif type_of_match == 'Pool system':
                type = 2
            else:
                type = 3
            number_of_teams = int(request.POST.get('number_of_teams'))
            number_of_days = int(request.POST.get('number_of_days'))
            matches_per_day = int(request.POST.get('matches_per_day'))
            # Our conventions
            # 1. League matches
            # 2. Pool System
            # 3. Knockout

            # League matches
            if type == 1:
                number_of_matches = (number_of_teams * (number_of_teams - 1) / 2)
                minimum_days = int(math.ceil(number_of_matches / matches_per_day))

                if number_of_days < minimum_days:
                    return HttpResponse(
                        "Sorry Matches cant be schedule in " + str(
                            number_of_days) + " days but can be scheduled in " + str(
                            minimum_days))
                odd = False

                new_user = LoginCredential(user_name=user_name, password=password, matches_per_day=matches_per_day,
                                           number_of_team=number_of_teams, type=type, number_of_pool=1)
                new_user.save()
                new_pool = Pool(login=new_user, pool_number=1)
                new_pool.save()
                user_id = new_user.id
                if number_of_teams % 2 == 1:
                    odd = True
                    number_of_teams += 1
                # group1=["pune warriors india","Mumbai Indian","King X1 punjab","Sunrise Hyderbad"]
                # group2=["Rising Pune Supergaints","Chennai king","Kolkalta Kinight rider","Delhi devils"]
                for i in range(1, int(number_of_teams / 2) + 1):
                    group1.append("Team" + str(i))
                    group2.append("Team" + str(i + int(number_of_teams / 2)))

                # print(group1)
                # print(group2)
                for i in range(number_of_teams - 1):
                    list1.extend(group1)
                    list2.extend(group2)
                    group1.insert(1, group2[0])
                    group2.remove(group2[0])
                    group2.append(group1[int(number_of_teams / 2)])
                    group1.remove(group1[int(number_of_teams / 2)])

                all_new_teams = []
                for team in group1:
                    all_new_teams.append(Point(pool=new_pool, team=team))

                for team in group2[:-1]:
                    all_new_teams.append(Point(team=team, pool=new_pool))
                # Using bulk_create instead of saving team every time
                # It uses only one query to save all teams
                # Silimarly for all the matches we used save n*(n-1)/2 times but now will use only 1 query
                # Very much optimized
                Point.objects.bulk_create(all_new_teams)

                if not odd:
                    new_team = Point(team=group2[len(group2) - 1], pool=new_pool)
                    new_team.save()
                if odd:
                    index = list1.index("Team" + str(number_of_teams))
                    while index:
                        list1.pop(index)
                        list2.pop(index)
                        try:
                            index = list1.index("Team" + str(number_of_teams))
                        except:
                            break

                    index = list2.index("Team" + str(number_of_teams))
                    while index:
                        list1.pop(index)
                        list2.pop(index)
                        try:
                            index = list2.index("Team" + str(number_of_teams))
                        except:
                            break
                # all_matches = zip(list1,list2)
                # print(minimum_days)
                # print(matches_per_day)
                # print(list1)
                # print(list2)
                new_matches = []
                for i in range(len(list1)):
                    new_matches.append(Match(team1=list1[i], team2=list2[i], pool=new_pool))
                    #print(new_matches[i].id)
                Match.objects.bulk_create(new_matches)
                # match_id_list = list(Match.objects.filter(login=new_user).values_list('id', flat=True))
                # print(match_id_list)
                # Set user id for this session
                # Acess using (user_id = request.session['user_id'])
                request.session['user_id'] = user_id
                return HttpResponseRedirect('/schedule/')
            # Pool system
            elif type == 2:
                if (number_of_teams >= 8):
                    if (number_of_teams % 3 == 0 or number_of_teams % 4 == 0 or number_of_teams % 5 == 0):

                        team_per_pool = 0
                        if number_of_teams % 6 == 0:
                            team_per_pool = 6
                        elif number_of_teams % 5 == 0:
                            team_per_pool = 5
                        elif number_of_teams % 4 == 0:
                            team_per_pool = 4
                        elif number_of_teams % 3 == 0:
                            team_per_pool = 3
                        number_of_pool = int(number_of_teams / team_per_pool)
                        number_of_matches = int(
                            (team_per_pool * (team_per_pool - 1)) / 2) * number_of_pool
                        new_user = LoginCredential(user_name=user_name, password=password,
                                                   matches_per_day=matches_per_day,
                                                   number_of_team=number_of_teams,
                                                   type=type,
                                                   number_of_pool=number_of_pool)
                        new_user.save()
                        new_pool = []
                        new_points_table = []
                        for i in range(number_of_pool):
                            new_pool += [Pool(login=new_user, pool_number=i + 1)]
                            # print(new_pool[i].pk)
                        Pool.objects.bulk_create(new_pool)

                        all_teams = []
                        for i in range(1, number_of_teams + 1):
                            all_teams.append("Team" + str(i))
                        # all_teams = group1 + group2
                        # print(all_teams)
                        all_pool = Pool.objects.filter(login=new_user)
                        for i in range(number_of_pool):
                            for j in range(team_per_pool):
                                # print(new_pool[i].id)
                                new_points_table += [Point(pool=all_pool[i], team=all_teams[i * team_per_pool + j])]
                                # print(str(i) + ' ' + all_teams[i * team_per_pool + j])
                        Point.objects.bulk_create(new_points_table)
                        new_matches = []
                        list1 = []
                        list2 = []
                        for i in range(number_of_pool):
                            zipped_list = round_robin(
                                list(Point.objects.filter(pool=all_pool[i]).values_list('team', flat=True)))
                            for team1, team2 in zipped_list:
                                print(team1 + "v/s" + team2)
                                list1.append(team1)
                                list2.append(team2)
                                new_matches.append(Match(pool=all_pool[i], team1=team1, team2=team2))

                        Match.objects.bulk_create(new_matches)
                        user_id = new_user.id
                        rows = int(math.floor(number_of_pool / 2))
                        extra = 0
                        if number_of_pool % 2 == 1:
                            extra = number_of_pool - 1
                        request.session['user_id'] = user_id

                        return HttpResponseRedirect('/schedule/0')

                    else:
                        return HttpResponse("Number of teams should be multiple of 3 or 4 or 5")
                else:
                    return HttpResponse("You need at least 8 teams for pool system")
            else:
                return HttpResponse("Something went Wrong")
        elif request.POST.get('Pool'):
            pool_number = request.POST.get('Pool')
            return HttpResponseRedirect('/schedule/' + str(pool_number))
        else:
            return HttpResponse("Something went wrong")
    else:
        user_id = request.session.get('user_id', 0)
        if not user_id:
            return HttpResponse("Something went wrong.")
        # print(user_id)
        user_obj = LoginCredential.objects.get(id=user_id)
        number_of_teams = user_obj.number_of_team
        pool_obj = Pool.objects.filter(login=user_obj)
        user_name = user_obj.user_name
        number_of_pool = user_obj.number_of_pool
        print('pool' + str(pool_number))
        if number_of_pool == 1 or pool_number:
            matches_per_day = user_obj.matches_per_day
            team_per_pool = int(number_of_teams / number_of_pool)
            number_of_matches = (team_per_pool * (team_per_pool - 1) / 2)
            minimum_days = int(math.ceil(number_of_matches / matches_per_day))

            match_obj_rows = pool_obj[pool_number-1].match_set
            match_id_list = match_obj_rows.values_list('id', flat=True)
            list1 = list(match_obj_rows.values_list('team1', flat=True))
            list2 = list(match_obj_rows.values_list('team2', flat=True))
            return render(request, 'home/schedule.html/',
                          {
                              'number_of_days': range(minimum_days),
                              'matches_per_day_list': range(matches_per_day), 'list1': list1, 'list2': list2,
                              'match_id': match_id_list,
                              'matches_per_day': matches_per_day, 'user_name': user_name, 'user_id': user_id,
                              'pool_number': pool_number,
                          })
        else:
            rows = int(math.floor(number_of_pool / 2))
            team_per_pool = int(number_of_teams / number_of_pool)
            all_teams = []
            for pool in pool_obj:
                all_teams += pool.point_set.values_list('team', flat=True)
            print(all_teams)
            extra = 0
            if number_of_pool % 2 == 1:
                extra = number_of_pool - 1
            return render(request, 'home/pool.html', {
                'rows': range(rows),
                'max': team_per_pool,
                'all_teams': all_teams,
                'team_per_pool': range(team_per_pool),
                'extra': extra,
            })


#
# return HttpResponse(
#     "Something seriously went wrong."
#     "Please mail at 'rshahshah2890@gmail.com when you get this error,"
#     "also explain the situation when you got this error'")


def test_send_email(request):
    message = 'This is a test message from rahul shah.Please reply if got.'
    subject = 'Rahul Shah (Test mail from Django)'
    from_email = settings.EMAIL_HOST
    to_email = [
        from_email,
        'siddheshkand123@gmail.com'
    ]
    # 'raunak3434@gmail.com',
    # 'omkarsarkate22@gmail.com',
    # 'shibashismallik@gmail.com',
    send_mail(subject, message, from_email, to_email, fail_silently=False)

    return HttpResponse("Successfully send")


def home_page(request):
    return render(request, "home/home_page.html")


def points_table(request, pool_number):
    user_id = request.session['user_id']
    user_obj = LoginCredential.objects.get(id=user_id)
    # print(user_id)
    pool_obj = user_obj.pool_set.get(pool_number=pool_number)

    full_table = pool_obj.point_set.order_by('-wins').all
    print(full_table)
    return render(request, 'home/points_table.html', {
        'full_table': full_table,
        'pool_number': pool_number,
    })


def round_robin(all_teams):
    number_of_teams = len(all_teams)
    odd = False
    if number_of_teams % 2 == 1:
        odd = True
        number_of_teams += 1
        all_teams += ['dummy']
    group1 = []
    group2 = []
    list1 = []
    list2 = []
    for i in range(int(number_of_teams / 2)):
        group1 += [all_teams[i]]
        group2 += [all_teams[i + int(number_of_teams / 2)]]

    for i in range(number_of_teams - 1):
        list1.extend(group1)
        list2.extend(group2)
        group1.insert(1, group2[0])
        group2.remove(group2[0])
        group2.append(group1[int(number_of_teams / 2)])
        group1.remove(group1[int(number_of_teams / 2)])

    if odd:
        index = list1.index('dummy')
        while index:
            list1.pop(index)
            list2.pop(index)
            try:
                index = list1.index('dummy')
            except:
                break

        index = list2.index('dummy')
        while index:
            list1.pop(index)
            list2.pop(index)
            try:
                index = list2.index('dummy')
            except:
                break
    list3 = list(zip(list1, list2))
    # print(list3)
    return list3
