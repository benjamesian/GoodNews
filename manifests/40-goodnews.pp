# Configure the goodnews service

service {'goodnews.service':
  ensure    => running,
  enable    => true,
  require   => File['goodnews.service'],
  subscribe => Exec['reload'],
}

file {'goodnews.service':
  ensure => file,
  mode   => '0644',
  owner  => 'root',
  group  => 'root',
  path   => '/etc/systemd/system/goodnews.service',
  source => '/data/current/etc/systemd/system/goodnews.service',
  notify => Exec['reload'],
}

exec {'reload':
  command => 'systemctl daemon-reload',
  path    => '/usr/bin:/bin',
}

exec {'restart':
  command => 'systemctl restart nginx.service',
  path    => '/usr/bin:/bin',
  require => [Exec['reload'], Service['goodnews.service']],
}
