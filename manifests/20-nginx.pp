# Configure nginx to serve the current release of GoodNews
# NOTE: this will be configured as the default server

package {'nginx':
  ensure => installed,
}

service {'nginx.service':
  ensure    => running,
  enable    => true,
  subscribe => [File['sites-enabled'], File['sites-disabled']],
}

file {'sites-disabled':
  ensure  => absent,
  path    => '/etc/nginx/sites-enabled/default',
  require => Package['nginx'],
}

file {'sites-available':
  ensure  => file,
  mode    => '0644',
  owner   => 'root',
  group   => 'root',
  path    => '/etc/nginx/sites-available/goodnews',
  source  => '/data/current/etc/nginx/sites-available/goodnews',
  require => Package['nginx'],
}

file {'sites-enabled':
  ensure  => link,
  path    => '/etc/nginx/sites-enabled/goodnews',
  target  => '../sites-available/goodnews',
  require => File['sites-available'],
}

exec {'restart':
  command => 'systemctl restart nginx.service',
  path    => '/usr/bin:/bin',
  require => [Service['nginx.service']],
}
