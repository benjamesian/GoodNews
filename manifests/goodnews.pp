# Set up the language processing service on a server

service {'goodnews.service':
  ensure    => running,
  enable    => true,
  require   => File['goodnews.service'],
  subscribe => Exec['daemon-reload'],
}

file {'goodnews.service':
  ensure => file,
  path   => '/etc/systemd/system/goodnews.service',
  source => '/data/current/etc/systemd/system/goodnews.service',
  mode   => '0644',
  owner  => 'root',
  group  => 'root',
  notify => Exec['daemon-reload'],
}

exec {'daemon-reload':
  command     => 'systemctl daemon-reload',
  path        => '/usr/bin:/bin',
  refreshonly => true,
}
